from pydantic import BaseModel, Field


class Location(BaseModel):
    region: str
    lat: float | None = None
    lon: float | None = None


class ClimateRecordResponse(BaseModel):
    id: str
    source_type: str
    location: Location
    timestamp: str
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    humidity_pct: float | None = None
    co2_ppm: float | None = None
    is_anomaly: bool = False
    is_archived: bool = False
    ingestion_id: str | None = None
    created_at: str


class PaginatedClimateRecords(BaseModel):
    items: list[ClimateRecordResponse]
    total: int
    page: int
    limit: int


class ClimateSummaryItem(BaseModel):
    region: str
    period: str
    avg_temperature_c: float | None = None
    total_precipitation_mm: float | None = None
    record_count: int
    anomaly_count: int


class ClimateSummaryResponse(BaseModel):
    items: list[ClimateSummaryItem]