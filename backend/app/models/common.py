from pydantic import BaseModel


class HealthResponse(BaseModel):
    mongo: str
    hdfs: str
    yarn: str


class MetricsResponse(BaseModel):
    request_count: int
    jobs_by_status: dict[str, int]
    active_alert_rules: int