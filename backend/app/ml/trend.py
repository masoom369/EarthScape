"""Linear Regression 30-day temperature forecast per region."""

from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from sklearn.linear_model import LinearRegression

_EPOCH = datetime(2020, 1, 1, tzinfo=UTC)


def train_trend_model(records: list[dict]) -> dict[str, Any]:
    """
    Train per-region Linear Regression on daily mean temperature.

    Input:  climate_record dicts with location.region, timestamp, temperature_c.
    Output: forecast_data — 30 daily predictions per region; accuracy_score is mean R².
    """
    by_region: dict[str, list[tuple[float, float]]] = {}

    for rec in records:
        region = rec.get("location", {}).get("region")
        temp = rec.get("temperature_c")
        ts = rec.get("timestamp")
        if not region or temp is None or ts is None:
            continue
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        day_num = float((ts - _EPOCH).days)
        by_region.setdefault(region, []).append((day_num, float(temp)))

    forecast_data: list[dict] = []
    r2_scores: list[float] = []

    for region, points in by_region.items():
        if len(points) < 5:
            continue
        X = np.array([p[0] for p in points]).reshape(-1, 1)
        y = np.array([p[1] for p in points])
        model = LinearRegression()
        model.fit(X, y)
        r2_scores.append(float(model.score(X, y)))

        last_day = max(p[0] for p in points)
        for i in range(1, 31):
            future_day = last_day + i
            pred = float(model.predict([[future_day]])[0])
            date = _EPOCH + timedelta(days=int(future_day))
            forecast_data.append({
                "region": region,
                "date": date.isoformat(),
                "forecast_temp_c": round(pred, 2),
            })

    accuracy = round(float(np.mean(r2_scores)), 4) if r2_scores else None

    return {"forecast_data": forecast_data, "predictions": [], "accuracy_score": accuracy}