import asyncio
import io
import json
import subprocess
from pathlib import Path
from typing import Any

import structlog

from app.config import get_settings
from app.hadoop.webhdfs import WebHDFSClient

logger = structlog.get_logger()

MAPREDUCE_DIR = Path(__file__).parent.parent.parent / "mapreduce"


class MapReduceRunner:
    def __init__(self):
        self.hdfs = WebHDFSClient()
        self.settings = get_settings()

    def _run_pipeline(self, job_type: str, input_data: str) -> str:
        """
        Execute mapper | sort | reducer as a local subprocess pipeline.
        Mirrors exactly what Hadoop Streaming does — mapper emits key\tvalue,
        sort groups by key, reducer aggregates. Pure Python, no YARN dependency.
        """
        script_dir = MAPREDUCE_DIR / job_type
        mapper = str(script_dir / "mapper.py")
        reducer = str(script_dir / "reducer.py")

        # mapper
        map_proc = subprocess.run(
            ["python", mapper],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if map_proc.returncode != 0:
            raise RuntimeError(f"Mapper failed: {map_proc.stderr[:500]}")

        # sort (simulate Hadoop shuffle/sort by key)
        sorted_lines = sorted(map_proc.stdout.splitlines())
        sorted_input = "\n".join(sorted_lines)

        # reducer
        red_proc = subprocess.run(
            ["python", reducer],
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
        Read input from HDFS, run local mapper|sort|reducer pipeline,
        write output back to HDFS. Returns (pseudo_app_id, hdfs_output_path).
        """
        output_path = f"/earthscape/processed/mapreduce/{job_type}/{job_id}"

        logger.info(
            "mapreduce_local_start",
            job_id=job_id,
            job_type=job_type,
            hdfs_input=hdfs_input_path,
        )

        # Read input file from HDFS
        input_data = await self.hdfs.read_file(hdfs_input_path)

        # Run pipeline in thread pool — subprocess.run blocks
        loop = asyncio.get_running_loop()
        output = await loop.run_in_executor(
            None, self._run_pipeline, job_type, input_data
        )

        # Write output back to HDFS
        await self.hdfs.mkdir(output_path)
        output_bytes = output.encode("utf-8")
        await self.hdfs.upload_file(f"{output_path}/part-00000", output_bytes, overwrite=True)

        logger.info(
            "mapreduce_local_done",
            job_id=job_id,
            output_lines=output.count("\n"),
        )

        # Return a pseudo app_id — job_service.trigger_mapreduce uses this only for logging
        return f"local-{job_id}", output_path