from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "running", "completed", "failed"]
MapReduceJobType = Literal["temperature_agg", "precipitation_totals", "anomaly_scores"]
MLModelType = Literal["anomaly_detection", "trend_prediction", "correlation"]


class MapReduceJobRequest(BaseModel):
    job_name: str = Field(min_length=1)
    hdfs_input_path: str = Field(min_length=1)
    job_type: MapReduceJobType


class MLTrainRequest(BaseModel):
    model_type: MLModelType


class JobLogResponse(BaseModel):
    id: str
    job_type: str
    job_name: str
    status: str
    hdfs_input: str | None = None
    hdfs_output: str | None = None
    duration_seconds: int | None = None
    triggered_by: str
    started_at: str
    completed_at: str | None = None
    error: str | None = None


class PaginatedJobLogs(BaseModel):
    items: list[JobLogResponse]
    total: int
    page: int
    limit: int
