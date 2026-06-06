from typing import Literal

from pydantic import BaseModel, Field

AlertMetric = Literal["temperature_c", "precipitation_mm", "co2_ppm", "humidity_pct"]
AlertOperator = Literal[">", "<", "=", ">=", "<="]
AlertSeverity = Literal["low", "medium", "high"]


class AlertRuleCreate(BaseModel):
    name: str = Field(min_length=1)
    metric: AlertMetric
    operator: AlertOperator
    threshold: float
    severity: AlertSeverity


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    metric: AlertMetric | None = None
    operator: AlertOperator | None = None
    threshold: float | None = None
    severity: AlertSeverity | None = None
    is_active: bool | None = None


class AlertRuleResponse(BaseModel):
    id: str
    name: str
    metric: str
    operator: str
    threshold: float
    severity: str
    is_active: bool
    created_by: str
    created_at: str


class AlertEventResponse(BaseModel):
    id: str
    rule_id: str
    climate_record_id: str
    triggered_value: float
    severity: str
    acknowledged: bool
    acknowledged_by: str | None = None
    triggered_at: str
    notification_log: dict | None = None


class PaginatedAlertEvents(BaseModel):
    items: list[AlertEventResponse]
    total: int
    page: int
    limit: int