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

# Seed runs process 82k+ records through a subprocess — 120s is too tight
# on slower machines. 600s gives headroom for both CSV job types without
# risking indefinite hangs (real hangs manifest as mapper producing no
# output, not as a slow but progressing run).
_SUBPROCESS_TIMEOUT = 600


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
        if suffix in (".json", ".geojson", ".ndjson"):
            return "json"
        raise MapReduceFormatError(
            f"Cannot determine format from input path '{hdfs_path}'. "
            "Expected a .csv, .json, .geojson, or .ndjson extension."
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
        sys.executable avoids Python 2 on systems where 'python' resolves to py2.
        """
        script_dir = MAPREDUCE_DIR / job_type
        mapper = str(script_dir / "mapper.py")
        reducer = str(script_dir / "reducer.py")

        map_proc = subprocess.run(
            [sys.executable, mapper],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=_SUBPROCESS_TIMEOUT,
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
            timeout=_SUBPROCESS_TIMEOUT,
        )
        if red_proc.returncode != 0:
            raise RuntimeError(f"Reducer failed: {red_proc.stderr[:500]}")

        return red_proc.stdout

    async def submit_job(
        self, job_id: str, job_type: str, job_name: str, hdfs_input_path: str
    ) -> tuple[str, str]:
        """
        Validate input format, confirm file exists on HDFS, read it, run
        local mapper|sort|reducer pipeline, write output back to HDFS.
        Returns (pseudo_app_id, hdfs_output_path).

        Raises MapReduceFormatError on format mismatch — fails before
        touching HDFS so the error is actionable, not a subprocess crash.
        Raises RuntimeError if the file doesn't exist on HDFS — prevents
        the misleading 404 from surfacing deep inside read_file_stream.
        """
        self._validate_format(job_type, hdfs_input_path)

        # Explicit existence check before streaming — read_file_stream raises
        # a generic RuntimeError on 404 which is hard to distinguish from a
        # network error. Checking first gives a clear message and skips the
        # DataNode redirect round-trip entirely when the file is absent.
        if not await self.hdfs.file_exists(hdfs_input_path):
            raise RuntimeError(
                f"HDFS input file not found: '{hdfs_input_path}'. "
                "Ensure the file was successfully ingested before running this job."
            )

        output_path = f"/earthscape/processed/mapreduce/{job_type}/{job_id}"

        logger.info(
            "mapreduce_local_start",
            job_id=job_id,
            job_type=job_type,
            hdfs_input=hdfs_input_path,
        )

        input_data = await self.hdfs.read_file(hdfs_input_path)

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
        """Convert a JSON array file to newline-delimited JSON for the mapper.
        No-op if content is already JSONL or a single object."""
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