from datetime import UTC, datetime

from bson import ObjectId

from app.db.mongo import get_db
from app.ml.anomaly import train_anomaly_model
from app.ml.correlation import train_correlation_model
from app.ml.trend import train_trend_model
from app.repositories.climate_repo import ClimateRepository
from app.repositories.ml_repo import MLRepository
from app.services.job_service import JobService

MODEL_DAYS = {
    "anomaly_detection": 90,
    "trend_prediction": 365,
    "correlation": 365,
}


class MLService:
    def __init__(self):
        db = get_db()
        self.climate_repo = ClimateRepository(db)
        self.ml_repo = MLRepository(db)
        self.job_service = JobService()

    async def train(self, model_type: str, user_id: str) -> dict:
        job_id = await self.job_service.create_ml_job_log(f"ml_{model_type}", user_id)
        start = datetime.now(UTC)
        try:
            await self.job_service.job_repo.update_status(job_id, "running")
            days = MODEL_DAYS.get(model_type, 90)
            records = await self.climate_repo.find_for_ml(days)

            if model_type == "anomaly_detection":
                result = train_anomaly_model(records)
                anomaly_ids = result.get("anomaly_record_ids", [])
                if anomaly_ids:
                    await self.climate_repo.bulk_update_anomaly_flags(anomaly_ids)
            elif model_type == "trend_prediction":
                result = train_trend_model(records)
            elif model_type == "correlation":
                result = train_correlation_model(records)
            else:
                raise ValueError(f"Unknown model type: {model_type}")

            duration = int((datetime.now(UTC) - start).total_seconds())
            ml_doc = {
                "model_type": model_type,
                "record_count": len(records),
                "accuracy_score": result.get("accuracy_score"),
                "predictions": result.get("predictions", []),
                "anomaly_record_ids": [
                    ObjectId(x) for x in result.get("anomaly_record_ids", [])
                    if ObjectId.is_valid(x)
                ],
                "correlation_matrix": result.get("correlation_matrix"),
                "forecast_data": result.get("forecast_data"),
                "job_id": job_id,
            }
            saved = await self.ml_repo.create(ml_doc)
            await self.job_service.complete_ml_job(job_id, "completed", duration)
            return saved
        except Exception as exc:
            duration = int((datetime.now(UTC) - start).total_seconds())
            await self.job_service.complete_ml_job(job_id, "failed", duration, str(exc))
            raise

    async def get_latest(self, model_type: str) -> dict | None:
        return await self.ml_repo.get_latest_by_type(model_type)
