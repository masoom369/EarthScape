from pydantic import BaseModel


class MLResultResponse(BaseModel):
    id: str
    model_type: str
    trained_at: str
    record_count: int
    accuracy_score: float | None = None
    predictions: list[dict] = []
    anomaly_record_ids: list[str] = []
    correlation_matrix: dict | None = None
    forecast_data: list[dict] | None = None
    job_id: str | None = None
