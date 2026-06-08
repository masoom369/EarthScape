import structlog
from bson import ObjectId

from app.db.mongo import get_db
from app.repositories.alert_repo import AlertRepository
from app.services.alert_service import AlertService

logger = structlog.get_logger()

VALID_OPERATORS = {">", "<", "=", ">=", "<="}
_FLOAT_EPSILON = 1e-9  # MINOR #29: safe float equality tolerance


def _evaluate(value: float, operator: str, threshold: float) -> bool:
    match operator:
        case ">":
            return value > threshold
        case "<":
            return value < threshold
        case "=":
            # MINOR #29: never use == on floats; use epsilon comparison
            return abs(value - threshold) < _FLOAT_EPSILON
        case ">=":
            return value >= threshold
        case "<=":
            return value <= threshold
        case _:
            return False


async def evaluate_record_alerts(record: dict, inserted_id: str) -> list[dict]:
    """
    Evaluate active alert rules against one ingested climate record.

    inserted_id: MongoDB _id string assigned after bulk_insert.
    CRITICAL #1/#4 fixed: climate_record_id stored as ObjectId for referential integrity.
    """
    alert_service = AlertService()
    rules = await alert_service.get_active_rules()
    if not rules:
        return []

    alert_repo = AlertRepository(get_db())
    events = []

    for rule in rules:
        metric = rule["metric"]
        value = record.get(metric)
        if value is None:
            continue
        if not _evaluate(float(value), rule["operator"], rule["threshold"]):
            continue

        rule_id = rule["_id"]
        notification = {
            "rule_name": rule["name"],
            "metric": metric,
            "triggered_value": value,
            "severity": rule["severity"],
            "record_id": inserted_id,
        }
        logger.info("alert_triggered", **notification)

        event = await alert_repo.create_event({
            "rule_id": ObjectId(rule_id) if ObjectId.is_valid(str(rule_id)) else rule_id,
            # CRITICAL #1: convert to ObjectId before insert — fixes $lookup / aggregation
            "climate_record_id": ObjectId(inserted_id) if ObjectId.is_valid(inserted_id) else inserted_id,
            "triggered_value": float(value),
            "severity": rule["severity"],
            "notification_log": notification,
        })
        events.append(event)

    return events