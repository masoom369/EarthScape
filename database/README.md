# EarthScape MongoDB Setup

MongoDB 7 runs **natively on the host** (not in Docker).

## Install & Start (Windows)

1. Download MongoDB Community Server 7 from https://www.mongodb.com/try/download/community
2. Install as a Windows service or run manually:
   ```powershell
   mongod --dbpath C:\data\db
   ```
3. Verify: `mongosh --eval "db.runCommand({ ping: 1 })"`

## Database

- **Name:** `earthscape` (set via `MONGO_DB` env var)
- **URI:** `mongodb://localhost:27017` (set via `MONGO_URI`)

## Collections

| Collection | Purpose |
|---|---|
| `users` | Accounts and roles |
| `climate_records` | Climate sensor/station/satellite data |
| `ingestion_logs` | File upload audit trail |
| `job_logs` | MapReduce and ML job status |
| `ml_results` | Model outputs |
| `alert_rules` | Threshold alert definitions |
| `alert_events` | Triggered alerts |
| `support_tickets` | User support requests |
| `revoked_tokens` | JWT revocation (TTL index) |

## Indexes

Indexes are created automatically when the FastAPI backend starts (`app/db/mongo.py` → `create_indexes()`).

To verify indexes after starting the backend:
```javascript
use earthscape
db.climate_records.getIndexes()
```

## Seed Data

From the `backend` directory:
```powershell
python scripts/generate_seed_data.py   # one-time: creates seed_data/ files
python scripts/seed.py --file seed_data/weather_stations_2023.csv
python scripts/seed.py --file seed_data/sensor_realtime_sample.json
python scripts/seed.py --file seed_data/satellite_metadata_q1_2024.json
```

## Default Admin User

Created on first backend startup if no users exist:
- Email: `admin@earthscape.local`
- Password: `Admin123!` (change immediately in production)

## Backup

Daily cron (Linux/macOS) or Task Scheduler (Windows):
```
0 2 * * * /path/to/backend/scripts/backup.sh
```
