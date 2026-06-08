"""Isolation Forest anomaly detection on temperature and precipitation."""

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


def train_anomaly_model(records: list[dict]) -> dict[str, Any]:
    """
    Train Isolation Forest on temperature_c and precipitation_mm.
    MAJOR #13: records missing BOTH metrics are dropped entirely.
    Records missing only one metric are also dropped — imputing 0.0 skews z-scores
    and treats absence as an extreme low value, producing false anomaly signals.
    Callers must pass sufficient records (>=10) after filtering for meaningful results.
    """
    features: list[list[float]] = []
    ids: list[str] = []

    for rec in records:
        temp = rec.get("temperature_c")
        precip = rec.get("precipitation_mm")
        # MAJOR #13 fix: require both fields; drop records where either is missing
        if temp is None or precip is None:
            continue
        features.append([float(temp), float(precip)])
        ids.append(str(rec["_id"]))

    if len(features) < 10:
        return {"predictions": [], "anomaly_record_ids": [], "accuracy_score": None}

    X = np.array(features)
    model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    labels = model.fit_predict(X)
    scores = model.decision_function(X)

    predictions: list[dict] = []
    anomaly_ids: list[str] = []

    for i, (label, score) in enumerate(zip(labels, scores, strict=True)):
        is_anomaly = label == -1
        predictions.append({
            "record_id": ids[i],
            "score": float(score),
            "is_anomaly": is_anomaly,
        })
        if is_anomaly:
            anomaly_ids.append(ids[i])

    anomaly_rate = len(anomaly_ids) / len(predictions) if predictions else 0.0
    accuracy = round(1.0 - abs(anomaly_rate - 0.05), 4)

    return {
        "predictions": predictions,
        "anomaly_record_ids": anomaly_ids,
        "accuracy_score": accuracy,
    }