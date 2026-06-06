"""Isolation Forest anomaly detection on temperature and precipitation."""

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


def train_anomaly_model(records: list[dict]) -> dict[str, Any]:
    """
    Train Isolation Forest on temperature_c and precipitation_mm.

    Input:  list of climate_record dicts with _id, temperature_c, precipitation_mm.
    Output: predictions list, anomaly_record_ids, accuracy_score (illustrative — measures
            how close detected rate is to contamination param, not true classification accuracy).
    """
    features: list[list[float]] = []
    ids: list[str] = []

    for rec in records:
        temp = rec.get("temperature_c")
        precip = rec.get("precipitation_mm")
        if temp is None and precip is None:
            continue
        features.append([
            float(temp) if temp is not None else 0.0,
            float(precip) if precip is not None else 0.0,
        ])
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

    # Illustrative metric: proximity of detected rate to contamination param
    anomaly_rate = len(anomaly_ids) / len(predictions) if predictions else 0.0
    accuracy = round(1.0 - abs(anomaly_rate - 0.05), 4)

    return {
        "predictions": predictions,
        "anomaly_record_ids": anomaly_ids,
        "accuracy_score": accuracy,
    }