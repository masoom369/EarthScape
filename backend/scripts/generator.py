import argparse
import csv
import json
import math
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

REGIONS = [
    {"name": "Karachi",    "lat": 24.8607, "lon": 67.0011},
    {"name": "Lahore",     "lat": 31.5204, "lon": 74.3587},
    {"name": "Islamabad",  "lat": 33.6844, "lon": 73.0479},
    {"name": "Quetta",     "lat": 30.1798, "lon": 66.9750},
    {"name": "Peshawar",   "lat": 34.0151, "lon": 71.5249},
]

REGION_BASELINE: dict[str, dict[str, float]] = {
    "Karachi":   {"temp": 28.0, "precip": 1.2,  "humidity": 72.0, "co2": 415.0},
    "Lahore":    {"temp": 25.0, "precip": 1.8,  "humidity": 60.0, "co2": 418.0},
    "Islamabad": {"temp": 20.0, "precip": 2.5,  "humidity": 55.0, "co2": 412.0},
    "Quetta":    {"temp": 18.0, "precip": 0.9,  "humidity": 40.0, "co2": 410.0},
    "Peshawar":  {"temp": 23.0, "precip": 1.5,  "humidity": 50.0, "co2": 416.0},
}

# Mirrors backend/app/db/seed.py's 5-year window so manually-uploaded bulk
# files sit on the same timeline as the auto-seeded Mongo data, just with a
# distinct RNG seed so they aren't byte-identical duplicates of seeded rows.
RANGE_START = date(2021, 1, 1)
RANGE_END = date(2025, 12, 31)
CO2_ANNUAL_DRIFT_PPM = 2.4

_rng = random.Random(7)


def _random_timestamp() -> datetime:
    span_days = (RANGE_END - RANGE_START).days
    offset_days = _rng.randint(0, span_days)
    day = RANGE_START + timedelta(days=offset_days)
    hour = _rng.choice([0, 4, 8, 12, 16, 20])
    return datetime(day.year, day.month, day.day, hour, tzinfo=UTC)


def _generate_record(region: dict[str, Any], source_type: str) -> dict:
    ts = _random_timestamp()
    baseline = REGION_BASELINE[region["name"]]
    day_of_year = ts.timetuple().tm_yday
    years_since_start = (ts.date() - RANGE_START).days / 365.25

    seasonal_offset = 8.0 * math.sin(2 * math.pi * day_of_year / 365)
    temp_jitter = (_rng.random() - 0.5) * 3.0
    precip_jitter = _rng.random() * 2.0
    humid_jitter = (_rng.random() - 0.5) * 8.0
    co2_jitter = (_rng.random() - 0.5) * 4.0

    temp = round(baseline["temp"] + seasonal_offset + temp_jitter, 2)
    precip = max(0.0, round(baseline["precip"] + precip_jitter if _rng.random() > 0.3 else 0.0, 2))
    humidity = min(100.0, max(0.0, round(baseline["humidity"] + humid_jitter, 1)))
    co2 = round(baseline["co2"] + (years_since_start * CO2_ANNUAL_DRIFT_PPM) + co2_jitter, 1)

    is_anomaly = _rng.random() < 0.01
    if is_anomaly:
        temp = round(temp + 18.0, 2)
        humidity = max(0.0, round(humidity - 25.0, 1))

    return {
        "region": region["name"],
        "source_type": source_type,
        "timestamp": ts.isoformat(),
        "temperature_c": temp,
        "precipitation_mm": precip,
        "humidity_pct": humidity,
        "co2_ppm": co2,
        "lat": region["lat"],
        "lon": region["lon"],
    }


def _write_csv(path: Path, records: list[dict]) -> None:
    """
    Column order matches what the MapReduce mappers read positionally:
    region@0, timestamp@1, temperature_c@2, precipitation_mm@3 — see
    mapreduce/temperature_agg/mapper.py and mapreduce/precipitation_totals/
    mapper.py, both use parts[0]/parts[2]/parts[3] directly, not by header
    name. IngestionService._parse_csv itself is header-name based (robust to
    column order), but the mapper scripts are not — matching this exact
    layout keeps both paths working.
    """
    fieldnames = [
        "region", "timestamp", "temperature_c", "precipitation_mm",
        "humidity_pct", "co2_ppm",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow({k: rec[k] for k in fieldnames})


def _write_json(path: Path, records: list[dict]) -> None:
    """
    JSON array shape matching IngestionService._parse_json_records, which
    reads `item.get("region")` with a fallback to `item["location"]["region"]`
    — both included here so the parser's branch logic is exercised either way.
    """
    payload = [
        {
            "region": rec["region"],
            "source_type": rec["source_type"],
            "timestamp": rec["timestamp"],
            "temperature_c": rec["temperature_c"],
            "precipitation_mm": rec["precipitation_mm"],
            "humidity_pct": rec["humidity_pct"],
            "co2_ppm": rec["co2_ppm"],
            "location": {"region": rec["region"], "lat": rec["lat"], "lon": rec["lon"]},
        }
        for rec in records
    ]
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def generate(output_dir: Path, count: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    def make_batch(source_type: str) -> list[dict]:
        batch = [_generate_record(_rng.choice(REGIONS), source_type) for _ in range(count)]
        batch.sort(key=lambda r: r["timestamp"])
        return batch

    weather_station = make_batch("weather_station")
    satellite = make_batch("satellite")
    sensor = make_batch("sensor")

    _write_csv(output_dir / "weather_stations_bulk.csv", weather_station)
    _write_csv(output_dir / "satellite_bulk.csv", satellite)
    _write_json(output_dir / "sensor_bulk.json", sensor)

    print(f"[producer] wrote {count} records each to {output_dir}/:")
    print(f"  weather_stations_bulk.csv  (CSV, weather_station)")
    print(f"  satellite_bulk.csv         (CSV, satellite)")
    print(f"  sensor_bulk.json           (JSON, sensor)")
    print()
    print("Upload these via the Ingest Data page (match Source Type to the")
    print("file). Once ingested, run from the Jobs page:")
    print("  weather_stations_bulk.csv -> Temperature Aggregation (CSV)")
    print("  satellite_bulk.csv        -> Precipitation Totals (CSV)")
    print("  sensor_bulk.json          -> Anomaly Scores (JSON)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate bulk climate dataset files for manual ingestion via the UI"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "seed_data",
        help="Directory to write files to (default: backend/seed_data/)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1000,
        help="Records per file (default: 1000)",
    )
    args = parser.parse_args()
    generate(args.output_dir, args.count)


if __name__ == "__main__":
    main()