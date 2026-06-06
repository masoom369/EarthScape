"""Generate seed data files for EarthScape demo (run once)."""

import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

REGIONS = ["Karachi", "Lahore", "Islamabad", "Quetta", "Peshawar"]
REGION_COORDS = {
    "Karachi": (24.8607, 67.0011),
    "Lahore": (31.5204, 74.3587),
    "Islamabad": (33.6844, 73.0479),
    "Quetta": (30.1798, 66.9750),
    "Peshawar": (34.0151, 71.5249),
}
SEED_DIR = Path(__file__).parent.parent / "seed_data"


def generate_weather_csv(n: int = 5000) -> None:
    start = datetime(2023, 1, 1)
    lines = ["region,timestamp,temperature_c,precipitation_mm,humidity_pct,co2_ppm"]
    for i in range(n):
        region = REGIONS[i % len(REGIONS)]
        ts = start + timedelta(hours=i * 2)
        temp = round(random.gauss(28, 8), 2)
        precip = round(max(0, random.gauss(2, 5)), 2)
        humidity = round(random.uniform(30, 90), 2)
        co2 = round(random.gauss(410, 15), 2)
        lines.append(f"{region},{ts.isoformat()}Z,{temp},{precip},{humidity},{co2}")
    (SEED_DIR / "weather_stations_2023.csv").write_text("\n".join(lines), encoding="utf-8")
    print(f"Created weather_stations_2023.csv ({n} records)")


def generate_sensor_json(n: int = 500) -> None:
    start = datetime(2024, 1, 1)
    records = []
    regional_temps: dict[str, list[float]] = {r: [] for r in REGIONS[:2]}

    for i in range(n):
        region = REGIONS[i % 2]
        ts = start + timedelta(hours=i * 4)
        temp = round(random.gauss(30, 5), 2)
        regional_temps[region].append(temp)
        record = {
            "record_id": str(uuid.uuid4()),
            "region": region,
            "timestamp": ts.isoformat() + "Z",
            "temperature_c": temp,
            "humidity_pct": round(random.uniform(40, 85), 2),
            "co2_ppm": round(random.gauss(415, 20), 2),
            "precipitation_mm": round(max(0, random.gauss(1, 3)), 2),
        }
        records.append(record)

    # Inject ~5% anomalies
    anomaly_count = max(1, n // 20)
    for idx in random.sample(range(n), anomaly_count):
        region = records[idx]["region"]
        mean = sum(regional_temps[region]) / len(regional_temps[region])
        records[idx]["temperature_c"] = round(mean + random.uniform(20, 30), 2)
        records[idx]["_injected_anomaly"] = True

    with open(SEED_DIR / "sensor_realtime_sample.json", "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"Created sensor_realtime_sample.json ({n} records, {anomaly_count} anomalies)")


def generate_satellite_json(n: int = 200) -> None:
    start = datetime(2024, 1, 1)
    records = []
    for i in range(n):
        region = REGIONS[i % len(REGIONS)]
        lat, lon = REGION_COORDS[region]
        ts = start + timedelta(days=i)
        records.append({
            "source_type": "satellite",
            "region": region,
            "timestamp": ts.isoformat() + "Z",
            "location": {"region": region, "lat": lat, "lon": lon},
            "temperature_c": round(random.gauss(25, 6), 2),
            "precipitation_mm": round(max(0, random.gauss(0.5, 2)), 2),
            "humidity_pct": round(random.uniform(20, 80), 2),
            "co2_ppm": round(random.gauss(405, 10), 2),
        })
    (SEED_DIR / "satellite_metadata_q1_2024.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
    print(f"Created satellite_metadata_q1_2024.json ({n} records)")


if __name__ == "__main__":
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    generate_weather_csv()
    generate_sensor_json()
    generate_satellite_json()
