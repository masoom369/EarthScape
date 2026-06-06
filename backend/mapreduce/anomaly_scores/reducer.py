#!/usr/bin/env python3
import json
import math
import sys

THRESHOLD = 2.5
METRICS = ["temperature_c", "humidity_pct", "co2_ppm"]
DEFAULT_FILL = -9999

current_region: str | None = None
records: list[dict] = []


def emit_results(region: str, recs: list[dict]) -> None:
    if not recs:
        return
    stats: dict[str, tuple[float, float]] = {}
    for m in METRICS:
        vals = [r.get(m) for r in recs if r.get(m) is not None]
        if vals:
            mean = sum(vals) / len(vals)
            variance = sum((v - mean) ** 2 for v in vals) / len(vals)
            stats[m] = (mean, math.sqrt(variance) if variance > 0 else 0.0)
    for rec in recs:
        scores = []
        for m in METRICS:
            val = rec.get(m)
            if val is None or m not in stats:
                continue
            mean, std = stats[m]
            z = (val - mean) / std if std > 0 else 0.0
            scores.append(abs(z))
        max_z = max(scores) if scores else 0.0
        print(json.dumps({
            "record_id": rec.get("record_id", ""),
            "anomaly_score": round(max_z, 4),
            "is_anomaly": max_z > THRESHOLD,
            "filled": any(rec.get(m) is None for m in METRICS),
        }))


for line in sys.stdin:
    region, rec_json = line.strip().split("\t", 1)
    if current_region and region != current_region:
        emit_results(current_region, records)
        records = []
    current_region = region
    rec = json.loads(rec_json)
    for m in METRICS:
        if rec.get(m) is None:
            rec[m] = DEFAULT_FILL
            rec["filled_flag"] = True
    records.append(rec)

if current_region:
    emit_results(current_region, records)