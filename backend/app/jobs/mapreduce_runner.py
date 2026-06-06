from pathlib import Path
from typing import Any

from app.config import get_settings
from app.hadoop.webhdfs import WebHDFSClient
from app.hadoop.yarn import YARNClient

MAPREDUCE_DIR = Path(__file__).parent.parent.parent / "mapreduce"


class MapReduceRunner:
    def __init__(self):
        self.hdfs = WebHDFSClient()
        self.yarn = YARNClient()
        self.settings = get_settings()

    async def _upload_scripts(self, job_type: str) -> None:
        """Upload mapper and reducer to HDFS before job submission."""
        script_dir = MAPREDUCE_DIR / job_type
        hdfs_dir = f"/earthscape/scripts/{job_type}"
        await self.hdfs.mkdir(hdfs_dir)
        for script in ("mapper.py", "reducer.py"):
            content = (script_dir / script).read_bytes()
            await self.hdfs.upload_file(f"{hdfs_dir}/{script}", content, overwrite=True)

    async def _resource_entry(self, hdfs_path: str) -> dict[str, Any]:
        """Fetch HDFS file metadata for YARN local-resource descriptor."""
        status = await self.hdfs.get_file_status(hdfs_path)
        if not status:
            raise RuntimeError(f"Cannot get HDFS status for {hdfs_path}")
        return {
            "resource": (
                f"hdfs://{self.settings.hdfs_namenode_host}:8020{hdfs_path}"
            ),
            "type": "FILE",
            "visibility": "APPLICATION",
            "size": status["length"],
            "timestamp": status["modificationTime"],
        }

    async def submit_job(
        self, job_id: str, job_type: str, job_name: str, hdfs_input_path: str
    ) -> tuple[str, str]:
        """
        Upload scripts, build YARN payload, submit Streaming job.
        Returns (yarn_application_id, hdfs_output_path).
        """
        await self._upload_scripts(job_type)

        output_path = f"/earthscape/processed/mapreduce/{job_type}/{job_id}"
        streaming_jar = self.settings.hadoop_streaming_jar

        new_app = await self.yarn.new_application()
        app_id: str = new_app["application-id"]

        mapper_hdfs = f"/earthscape/scripts/{job_type}/mapper.py"
        reducer_hdfs = f"/earthscape/scripts/{job_type}/reducer.py"

        mapper_res = await self._resource_entry(mapper_hdfs)
        reducer_res = await self._resource_entry(reducer_hdfs)
        jar_res = await self._resource_entry(streaming_jar)

        command = (
            f"hadoop jar hadoop-streaming.jar "
            f"-input {hdfs_input_path} "
            f"-output {output_path} "
            f"-mapper mapper.py "
            f"-reducer reducer.py "
            f"-file mapper.py "
            f"-file reducer.py"
        )

        payload = {
            "application-id": app_id,
            "application-name": job_name,
            "application-type": "MAPREDUCE",
            "am-container-spec": {
                "commands": {"command": command},
                "local-resources": {
                    "entry": [
                        {"key": "mapper.py", "value": mapper_res},
                        {"key": "reducer.py", "value": reducer_res},
                        {
                            "key": "hadoop-streaming.jar",
                            "value": {**jar_res, "visibility": "PUBLIC"},
                        },
                    ]
                },
            },
            "resource": {"memory": 1024, "vCores": 1},
            "priority": {"priority": 1},
            "queue": "default",
            "unmanaged-AM": False,
        }

        await self.yarn.submit_application(payload)
        return app_id, output_path