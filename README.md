# EarthScape Climate Agency — Big Data Analytics Platform

Student academic project for ingesting, processing, analyzing, and visualizing climate data using Hadoop, FastAPI, React, and MongoDB.

## Architecture

| Component | Runtime | Port |
|---|---|---|
| React Frontend (Vite) | Native | 5173 |
| FastAPI Backend | Native Python 3.11 | 8000 |
| MongoDB 7 | Native host | 27017 |
| Hadoop (NameNode + DataNode + ResourceManager + NodeManager) | Docker Desktop | 9870, 8088 |

> **Note on MapReduce execution:** Hadoop containers run for HDFS storage and the
> WebHDFS/YARN health checks, but `JobsPage` MapReduce jobs execute as a **local
> subprocess pipeline** (`mapper.py | sort | reducer.py`), not as real YARN
> applications. This is a functional demo substitute for true distributed
> processing — see `backend/app/jobs/mapreduce_runner.py` for details. Datasets
> larger than available RAM will not process correctly in this mode.

## Prerequisites

- Windows 10/11 64-bit, 16 GB RAM recommended
- MongoDB 7 Community (native install)
- Python 3.11+
- Node.js 22+
- Docker Desktop (4 GB+ RAM allocated)

## Quick Start

### 1. MongoDB (Database)

```powershell
mongod --dbpath C:\data\db
```

See [database/README.md](database/README.md) for schema and index details.

### 2. Hadoop (Docker)

```powershell
docker compose up -d
```

### 3. Backend

```powershell
cd backend
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

Default admin: `admin@earthscape.com` / `Admin123!`

The backend auto-seeds 365 days of synthetic climate data (5 regions × 3
source types × 3 readings/day ≈ 16,400 records) on first boot if
`climate_records` is empty, then auto-trains all three ML models so
dashboard charts are populated immediately. No manual seed step is
required for a fresh database — `scripts/seed.py` below is only for
loading additional real datasets on top of the synthetic baseline.

### 4. Seed Additional Data (optional)

```powershell
python scripts/seed.py --file seed_data/weather_stations_2023.csv
```

### 5. Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173

## MapReduce Job Types & Required Input Format

Each job type's mapper expects a specific input format. The Jobs page only
lists ingested files matching the selected job type — submitting via the
API directly with a mismatched format now fails fast with an explicit
error (`MapReduceFormatError`) instead of a subprocess crash.

| Job Type | Required Format | Output |
|---|---|---|
| `temperature_agg` | CSV | min / max / mean temperature per region |
| `precipitation_totals` | CSV | monthly precipitation totals per region |
| `anomaly_scores` | JSON / JSONL | per-record Z-score anomaly rating |

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `MONGO_URI` | MongoDB connection string |
| `MONGO_DB` | Database name (default: earthscape) |
| `JWT_SECRET` | Min 32 chars |
| `JWT_EXPIRE_MINUTES` | Token lifetime |
| `HDFS_NAMENODE_HOST` | Hadoop host (localhost) |
| `HDFS_WEBHDFS_PORT` | WebHDFS port (9870) |
| `HDFS_DATANODE_REWRITE_HOST` | Host to rewrite WebHDFS DataNode redirects to. Set to your **host machine's LAN/Docker-bridge IP** (not `localhost`) if the FastAPI backend itself runs inside the Docker network rather than natively on the host. Set to empty string for remote/production Hadoop clusters where no rewrite is needed. |
| `YARN_RM_PORT` | YARN REST port (8088) — used only for the `/health` endpoint; MapReduce jobs do not submit through YARN in this build |
| `HADOOP_STREAMING_JAR` | Path to streaming JAR on HDFS (reserved for future real YARN submission; unused by the current local-subprocess runner) |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ALERT_CACHE_TTL_SECONDS` | Alert rule cache TTL |
| `REALTIME_PRODUCER_INTERVAL` | Producer script interval |
| `DEFAULT_ADMIN_EMAIL` | Auto-created admin email on first boot |
| `DEFAULT_ADMIN_PASSWORD` | Auto-created admin password on first boot |
| `ARCHIVE_THRESHOLD_DAYS` | Days after which records are eligible for archival |
| `MAPREDUCE_DEFAULT_FILL` | Sentinel value used by the anomaly_scores reducer for missing metrics |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | API base URL |
| `VITE_POLL_REALTIME_MS` | Real-time feed poll interval |
| `VITE_POLL_ALERTS_MS` | Alerts poll interval |
| `VITE_POLL_JOBS_MS` | Jobs poll interval |

## Known Limitations

- **MapReduce is local, not distributed.** See note under Architecture above.
- **Live Feed requires manually running `scripts/producer.py`.** There is no
  automated process supplying `source_type: sensor` records — without it,
  the Dashboard's Live Feed panel stays empty. Not included in
  `docker-compose.yml` or any scheduler; start it manually per the section
  below if you want to see live data.
- **WebHDFS DataNode redirect rewriting** assumes the FastAPI backend runs
  on the host machine, not inside the Docker network. See
  `HDFS_DATANODE_REWRITE_HOST` above if your topology differs.
- **Large file ingestion** (>~512 MB) may exhaust memory in the local
  MapReduce runner, since the entire input is buffered as a string before
  being piped to the mapper subprocess.

## Backup (Cron)

```bash
0 2 * * * /path/to/backend/scripts/backup.sh
```

Outputs to `/backups/YYYY-MM-DD/` via `mongodump`.

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Synthetic Data Producer

Required to populate the Dashboard's "Live Feed" panel — not started
automatically.

```powershell
cd backend
python scripts/producer.py --interval 10 --token <your-access_token-cookie-value>
```

Get `<your-access_token-cookie-value>` from your browser's dev tools
(Application → Cookies → `access_token`) after logging in.