"""Pearson correlation matrix across climate metrics."""

from typing import Any

import pandas as pd


def train_correlation_model(records: list[dict]) -> dict[str, Any]:
    """
    Compute Pearson correlation matrix for temperature, CO2, precipitation, humidity.

    Input:  climate_record dicts with optional metric fields.
    Output: correlation_matrix 4x4 keyed by metric name; predictions is always empty
            for this model type.
    """
    metrics = ["temperature_c", "co2_ppm", "precipitation_mm", "humidity_pct"]
    rows = []
    for rec in records:
        row = {m: rec.get(m) for m in metrics}
        if any(v is not None for v in row.values()):
            rows.append(row)

    if len(rows) < 5:
        return {"correlation_matrix": None, "predictions": [], "accuracy_score": None}

    df = pd.DataFrame(rows).dropna(how="all")
    corr = df.corr(method="pearson", min_periods=3)
    matrix = {
        m1: {
            m2: round(float(corr.loc[m1, m2]), 4) if pd.notna(corr.loc[m1, m2]) else None
            for m2 in metrics
        }
        for m1 in metrics
    }

    return {"correlation_matrix": matrix, "predictions": [], "accuracy_score": None}