import asyncio
import json
import subprocess
import sys
from pathlib import Path

import structlog

from app.config import get_settings
from app.hadoop.webhdfs import WebHDFSClient

logger = structlog.get_logger()

MAPREDUCE_DIR = Path(__file__).parent.parent.parent / "mapreduce"

# CRITICAL #3 fix: each job_type declares the input format its mapper expects.
# Runner validates the actual file extension against this before executing,
# instead of blindly piping raw bytes into a mapper that assumes one format.
JOB_TYPE_EXPECTED_FORMAT: dict[str, str] = {
    "temperature_agg": "csv",
    "precipitation_totals": "csv",
    "anomaly_scores": "json",
}


class MapReduceFormatError(RuntimeError):
    """Raised when hdfs_input_path extension doesn't match job_type's expected format."""


class MapReduceRunner:
    def __init__(self) -> None:
        self.hdfs = WebHDFSClient()
        self.settings = get_settings()

    def _detect_format(self, hdfs_path: str) -> str:
        suffix = Path(hdfs_path).suffix.lower()
        if suffix == ".csv":
            return "csv"
        if suffix in (".json", ".geojson"):
            return "json"
        raise MapReduceFormatError(
            f"Cannot determine format from input path '{hdfs_path}'. "
            "Expected a .csv, .json, or .geojson extension."
        )

    def _validate_format(self, job_type: str, hdfs_path: str) -> None:
        expected = JOB_TYPE_EXPECTED_FORMAT.get(job_type)
        if expected is None:
            raise MapReduceFormatError(f"Unknown job_type: {job_type}")
        actual = self._detect_format(hdfs_path)
        if actual != expected:
            raise MapReduceFormatError(
                f"Job type '{job_type}' requires {expected.upper()} input, "
                f"but '{hdfs_path}' is {actual.upper()}. "
                f"Select a {expected.upper()} file from the ingestion log, "
                f"or choose a job type matching this file's format."
            )

    def _run_pipeline(self, job_type: str, input_data: str) -> str:
        """
        Execute mapper | sort | reducer as a local subprocess pipeline.
        Mirrors Hadoop Streaming: mapper emits key\\tvalue, sort groups by key,
        reducer aggregates. Pure Python, no YARN dependency.
        CRITICAL #2 documented: input_data is the full file content as a string.
        For multi-GB datasets this will OOM. True fix requires real YARN submission
        with Hadoop Streaming JAR. This runner is a functional demo substitute.
        MAJOR #12: sys.executable instead of "python" — avoids Python 2 on systems
        where 'python' is not symlinked to Python 3.
        """
        script_dir = MAPREDUCE_DIR / job_type
        mapper = str(script_dir / "mapper.py")
        reducer = str(script_dir / "reducer.py")

        map_proc = subprocess.run(
            [sys.executable, mapper],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if map_proc.returncode != 0:
            raise RuntimeError(f"Mapper failed: {map_proc.stderr[:500]}")

        sorted_lines = sorted(map_proc.stdout.splitlines())
        sorted_input = "\n".join(sorted_lines)

        red_proc = subprocess.run(
            [sys.executable, reducer],
            input=sorted_input,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if red_proc.returncode != 0:
            raise RuntimeError(f"Reducer failed: {red_proc.stderr[:500]}")

        return red_proc.stdout

    async def submit_job(
        self, job_id: str, job_type: str, job_name: str, hdfs_input_path: str
    ) -> tuple[str, str]:
        """
        Validate input format against job_type, read from HDFS (streamed),
        run local mapper|sort|reducer pipeline, write output back to HDFS.
        Returns (pseudo_app_id, hdfs_output_path).
        Raises MapReduceFormatError before touching HDFS if format mismatches —
        fails fast with an actionable message instead of a subprocess crash.
        """
        self._validate_format(job_type, hdfs_input_path)

        output_path = f"/earthscape/processed/mapreduce/{job_type}/{job_id}"

        logger.info(
            "mapreduce_local_start",
            job_id=job_id,
            job_type=job_type,
            hdfs_input=hdfs_input_path,
        )

        input_data = await self.hdfs.read_file(hdfs_input_path)

        # anomaly_scores mapper requires one JSON object per line (JSONL), not a
        # JSON array. If the ingested file is a JSON array, normalize it here
        # rather than letting the mapper's per-line json.loads() blow up on line 1.
        if JOB_TYPE_EXPECTED_FORMAT[job_type] == "json":
            input_data = self._normalize_to_jsonl(input_data)

        loop = asyncio.get_running_loop()
        output = await loop.run_in_executor(
            None, self._run_pipeline, job_type, input_data
        )

        await self.hdfs.mkdir(output_path)
        output_bytes = output.encode("utf-8")
        await self.hdfs.upload_file(f"{output_path}/part-00000", output_bytes, overwrite=True)

        logger.info(
            "mapreduce_local_done",
            job_id=job_id,
            output_lines=output.count("\n"),
        )

        return f"local-{job_id}", output_path

    def _normalize_to_jsonl(self, content: str) -> str:
        """Convert a JSON array file to newline-delimited JSON for the mapper's
        per-line parser. No-op if content is already JSONL or a single object."""
        stripped = content.strip()
        if not stripped:
            return content
        if stripped[0] != "[":
            return content
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise MapReduceFormatError(
                f"Input file is not valid JSON: {exc}"
            ) from exc
        if not isinstance(parsed, list):
            return content
        return "\n".join(json.dumps(item) for item in parsed)