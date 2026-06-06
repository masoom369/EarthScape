import structlog

from app.db.mongo import get_db
from app.repositories.alert_repo import AlertRepository
from app.services.alert_service import AlertService

logger = structlog.get_logger()


def _evaluate(value: float, operator: str, threshold: float) -> bool:
    ops = {
        ">": value > threshold,
        "<": value < threshold,
        "=": value == threshold,
        ">=": value >= threshold,
        "<=": value <= threshold,
    }
    return ops.get(operator, False)


async def evaluate_record_alerts(record: dict) -> list[dict]:
    """Background task: evaluate incoming climate record against cached alert rules."""
    alert_service = AlertService()
    rules = await alert_service.get_active_rules()
    if not rules:
        return []

    alert_repo = AlertRepository(get_db())
    events = []
    record_id = record.get("_id") or record.get("id")

    for rule in rules:
        metric = rule["metric"]
        value = record.get(metric)
        if value is None:
            continue
        if _evaluate(float(value), rule["operator"], rule["threshold"]):
            notification = {
                "rule_name": rule["name"],
                "metric": metric,
                "triggered_value": value,
                "severity": rule["severity"],
                "record_id": str(record_id),
            }
            logger.info("alert_notification", **notification)
            event = await alert_repo.create_event({
                "rule_id": rule["_id"],
                "climate_record_id": record_id if hasattr(record_id, "__str__") else record_id,
                "triggered_value": float(value),
                "severity": rule["severity"],
                "notification_log": notification,
            })
            events.append(event)
    return events
