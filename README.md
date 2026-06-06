# EarthScape Climate Agency — Big Data Analytics Platform

Student academic project for ingesting, processing, analyzing, and visualizing climate data using Hadoop, FastAPI, React, and MongoDB.

## Architecture

| Component | Runtime | Port |
|---|---|---|
| React Frontend (Vite) | Native | 5173 |
| FastAPI Backend | Native Python 3.11 | 8000 |
| MongoDB 7 | Native host | 27017 |
| Hadoop (NameNode + DataNode) | Docker Desktop | 9870, 8088 |

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

### 4. Seed Data

```powershell
python scripts/generate_seed_data.py
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
| `YARN_RM_PORT` | YARN REST port (8088) |
| `HADOOP_STREAMING_JAR` | Path to streaming JAR on HDFS |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ALERT_CACHE_TTL_SECONDS` | Alert rule cache TTL |
| `REALTIME_PRODUCER_INTERVAL` | Producer script interval |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | API base URL |
| `VITE_POLL_REALTIME_MS` | Real-time feed poll interval |
| `VITE_POLL_ALERTS_MS` | Alerts poll interval |
| `VITE_POLL_JOBS_MS` | Jobs poll interval |

## Backup (Cron)

```bash
0 2 * * * /path/to/backend/scripts/backup.sh
```

Outputs to `/backups/YYYY-MM-DD/` via `mongodump`.

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Synthetic Data Producer

```powershell
cd backend
python scripts/producer.py --interval 10
```
