from pydantic import BaseModel


class IngestionLogResponse(BaseModel):
    id: str
    filename: str
    file_hash: str
    hdfs_path: str | None = None
    format: str
    record_count: int
    status: str
    error_message: str | None = None
    triggered_by: str
    created_at: str


class PaginatedIngestionLogs(BaseModel):
    items: list[IngestionLogResponse]
    total: int
    page: int
    limit: int