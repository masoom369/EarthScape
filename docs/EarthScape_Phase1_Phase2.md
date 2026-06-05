# EarthScape Climate Agency — Big Data Analytics Platform
## Phase 1: Requirements | Phase 2: System Design

---

# PHASE 1 — REQUIREMENTS

## 1.1 Project Scope

**Client:** EarthScape Climate Agency
**Purpose:** Build a big data platform to ingest, process, analyze, and visualize large-scale climate data collected from satellites, weather stations, and environmental sensors. The system uses Hadoop for distributed processing, Python FastAPI as the backend, React as the frontend, and MongoDB as the primary database. Only the Hadoop cluster runs inside Docker Desktop to limit hardware overhead. All other components run natively on the host machine.
**Type:** Student academic project (non-production simulation)

---

## 1.2 Actors

| Actor | Role |
|---|---|
| Administrator | Full system access. Manages users, roles, data sources, and alert configurations. |
| Analyst | Can ingest data, trigger processing jobs, run ML models, and view dashboards. Cannot manage users. |
| Viewer | Read-only access. Can view dashboards, charts, and reports only. |
| System (automated) | Handles scheduled data ingestion cycles, background alert evaluation, and job status polling. |

---

## 1.3 Constraints

| Constraint | Detail |
|---|---|
| Frontend | React 19+, TypeScript, Vite — runs natively on host |
| Backend | Python 3.13+, FastAPI — runs natively on host |
| Primary Database | MongoDB 7 — installed and running natively on host (not containerized) |
| Big Data Layer | Hadoop 3.x (HDFS + MapReduce via Hadoop Streaming) — runs inside Docker Desktop only |
| Containerization | Docker Desktop used exclusively for the Hadoop cluster (NameNode + DataNode) |
| Auth | JWT stored in httpOnly cookie |
| Scope | Student project — no production SLA, no live deployment required |

---

## 1.4 Functional Requirements

### FR-01 — User Authentication and Authorization

| ID | Requirement |
|---|---|
| FR-01-01 | The system shall support user registration with email, password, and role assigned by an administrator. |
| FR-01-02 | The system shall authenticate users using JWT tokens stored exclusively in httpOnly, SameSite=Strict cookies. |
| FR-01-03 | The system shall support three distinct roles: Administrator, Analyst, and Viewer. |
| FR-01-04 | Every protected API route shall verify the JWT token before processing the request. |
| FR-01-05 | Administrators shall be able to create, update, and deactivate user accounts. |
| FR-01-06 | Role-based access control shall enforce the following restrictions: Viewers cannot trigger jobs or upload data; Analysts cannot manage users or alert rules; only Administrators can access system configuration and user management. |
| FR-01-07 | All passwords shall be hashed using bcrypt before being stored in MongoDB. |
| FR-01-08 | The system shall support user logout by revoking the active token and storing the token ID (jti) in a revocation collection with a TTL index for automatic cleanup. |

---

### FR-02 — Data Ingestion

| ID | Requirement |
|---|---|
| FR-02-01 | The system shall support ingestion of climate datasets including satellite imagery metadata (JSON), weather station records (CSV), and environmental sensor readings (JSON). |
| FR-02-02 | The system shall support batch ingestion of historical datasets via file upload through the web interface. |
| FR-02-03 | The system shall support simulated real-time ingestion using a Python producer script that generates synthetic sensor JSON events at a configurable interval and posts them to the ingestion API. |
| FR-02-04 | The system shall validate file format and schema correctness before writing data to HDFS. |
| FR-02-05 | The system shall log each ingestion event in MongoDB with filename, status (pending, success, failed), record count, HDFS path, and triggering user. |
| FR-02-06 | The system shall accept the following file formats: CSV, JSON, GeoJSON. |
| FR-02-07 | The system shall prevent duplicate ingestion by computing a SHA-256 hash of each uploaded file and rejecting files whose hash already exists in the ingestion log. |

---

### FR-03 — Data Storage

| ID | Requirement |
|---|---|
| FR-03-01 | Raw climate datasets shall be stored in HDFS, organized by data source type and partitioned by year, month, and day. |
| FR-03-02 | Processed results from MapReduce jobs, machine learning model outputs, and aggregated summaries shall be stored in MongoDB. |
| FR-03-03 | User accounts, role definitions, ingestion logs, job logs, alert configurations, alert events, and support tickets shall all reside in MongoDB. |
| FR-03-04 | The Hadoop cluster shall operate in pseudo-distributed single-node mode within Docker Desktop with a replication factor of 1 (appropriate for student/local scope). |
| FR-03-05 | MongoDB collections that are queried by timestamp, location, or source type shall have compound indexes defined on those fields and created programmatically via Motor's `create_index` calls during application startup. |
| FR-03-06 | The system shall support soft-deletion of climate records using an `is_archived` boolean flag and a configurable threshold age. |

---

### FR-04 — Data Processing (Hadoop MapReduce)

| ID | Requirement |
|---|---|
| FR-04-01 | The system shall implement three MapReduce jobs: temperature aggregation by region, monthly precipitation totals by region, and anomaly scoring using Z-score per metric per region. |
| FR-04-02 | MapReduce jobs shall be implemented using Hadoop Streaming with Python mapper and reducer scripts. |
| FR-04-03 | The system shall handle missing or null values in input records by substituting a configurable default fill value and appending a flag field to the affected output record. |
| FR-04-04 | MapReduce job execution shall be triggerable via an authenticated API call restricted to Analyst and Administrator roles. |
| FR-04-05 | Job lifecycle status (queued, running, completed, failed) shall be tracked in MongoDB and updated in real time as the job progresses. |
| FR-04-06 | MapReduce output shall be written to a structured HDFS output path and a summary of results shall be stored in MongoDB for dashboard consumption. The `job_service.py` module is responsible for polling YARN until the application reaches FINISHED state, reading the HDFS `part-00000` output via WebHDFS, parsing result lines, and writing the parsed summary to the `ml_results` or `job_logs` MongoDB collection as appropriate. |

---

### FR-05 — Real-time Data Processing

| ID | Requirement |
|---|---|
| FR-05-01 | The system shall include a Python producer script located at `backend/scripts/producer.py` that continuously generates synthetic climate sensor readings (temperature, humidity, CO2, precipitation) as JSON and submits them to the ingestion API at a configurable interval (default: every 10 seconds). |
| FR-05-02 | Each incoming real-time record shall be stored immediately to the `climate_records` MongoDB collection with a precise timestamp. |
| FR-05-03 | The dashboard shall display the most recent real-time records in a live feed panel that automatically refreshes at a configurable polling interval controlled by the `VITE_POLL_REALTIME_MS` environment variable (default: 10000 ms). |
| FR-05-04 | Real-time records shall be stored in the same collection as batch-ingested records but tagged with `source_type: sensor` to allow independent querying without contention. |

---

### FR-06 — Machine Learning Models

| ID | Requirement |
|---|---|
| FR-06-01 | The system shall implement an anomaly detection model using the Isolation Forest algorithm (scikit-learn) trained on temperature and precipitation records from the past 90 days. |
| FR-06-02 | The system shall implement a trend prediction model using Linear Regression (scikit-learn) to produce a 30-day daily temperature forecast per region. |
| FR-06-03 | The system shall implement a correlation analysis that computes a Pearson correlation matrix across temperature, CO2, precipitation, and humidity fields. |
| FR-06-04 | Model training shall be triggerable via an authenticated API call restricted to Analyst and Administrator roles, with the model type specified in the request body. |
| FR-06-05 | All model outputs including predictions, anomaly flags, anomaly scores, correlation matrices, and forecast arrays shall be stored in MongoDB. |
| FR-06-06 | Models shall be retrained on demand using the latest available data in MongoDB at the time of the training request. Automatic scheduled retraining is deferred — on-demand only is appropriate for student scope. |
| FR-06-07 | Each training run shall log metadata in MongoDB including model type, training timestamp, number of records used, and accuracy score where applicable. |
| FR-06-08 | After anomaly detection training completes, `ml_service.py` shall iterate the flagged record IDs returned by the Isolation Forest model and call `climate_repo.bulk_update_anomaly_flags(record_ids)` to back-write `is_anomaly: true` to the corresponding `climate_records` documents. This call is made exclusively by the service layer; no route handler or ML script touches the repository directly. |

---

### FR-07 — Data Visualization

| ID | Requirement |
|---|---|
| FR-07-01 | The system shall provide an interactive dashboard displaying: a temperature trend line chart, a precipitation bar chart, an anomaly scatter plot with flagged points highlighted, and a correlation heatmap. |
| FR-07-02 | All dashboard charts shall support filtering by date range and by geographic region or data source type. |
| FR-07-03 | ML model forecast results shall be rendered as overlay forecast lines on the temperature trend chart, visually distinguished from historical data. |
| FR-07-04 | Records flagged as anomalies shall appear as color-coded markers (distinct color or shape) on the anomaly scatter plot. |
| FR-07-05 | Dashboard data shall refresh automatically based on configurable polling intervals defined in frontend environment variables. |
| FR-07-06 | The dashboard and all data pages shall be responsive and fully usable at a minimum viewport width of 1280 pixels. |
| FR-07-07 | Analysts and Administrators shall be able to export the currently filtered dataset from the Climate Explorer page as a CSV file. The export endpoint shall enforce a hard cap of 10,000 records per request; if the active filter resolves to more than 10,000 records, the API shall return HTTP 400 with a message instructing the user to narrow the filter criteria. |

---

### FR-08 — Notifications and Alerts

| ID | Requirement |
|---|---|
| FR-08-01 | Administrators shall be able to define alert rules specifying: the climate metric to monitor, a numeric threshold, a comparison operator (>, <, =, >=, <=), and a severity level (low, medium, high). |
| FR-08-02 | The system shall evaluate all active alert rules against each incoming real-time climate record immediately upon ingestion. Alert rules are served from an in-memory cache with a TTL controlled by `ALERT_CACHE_TTL_SECONDS`. |
| FR-08-03 | When an alert rule is triggered, the system shall create an alert event document in MongoDB recording the rule ID, triggering record ID, actual value, severity, and timestamp. |
| FR-08-04 | The dashboard shall display a notifications panel listing all unacknowledged alert events, updated via polling every `VITE_POLL_ALERTS_MS` milliseconds (default: 15000). |
| FR-08-05 | Email notification delivery shall be simulated in the student scope by logging the notification payload to the application log and storing it in MongoDB rather than dispatching a real email. |
| FR-08-06 | Any authenticated user shall be able to acknowledge an alert event, after which it will no longer appear in the active notifications panel. |
| FR-08-07 | When an alert rule is deactivated or deleted via `PATCH /alerts/rules/{id}` or `DELETE /alerts/rules/{id}`, the in-memory alert cache shall be invalidated immediately so the change takes effect on the next record ingested rather than waiting for the next TTL expiry cycle. |

---

### FR-09 — Feedback and Support

| ID | Requirement |
|---|---|
| FR-09-01 | Any authenticated user shall be able to submit a support ticket by providing a subject, a detailed description, and an optional screenshot URL. |
| FR-09-02 | Submitted tickets shall be stored in MongoDB with a status field initialized to `open`. |
| FR-09-03 | Administrators shall be able to view all tickets, update the status (open, in-progress, resolved), and add a written response. |
| FR-09-04 | Users who submitted a ticket shall be able to view the current status and any administrator response on their ticket list page. |

---

## 1.5 Non-Functional Requirements

### NFR-01 — Performance

| ID | Requirement |
|---|---|
| NFR-01-01 | API response time for dashboard aggregation queries shall not exceed 3 seconds under normal development load. |
| NFR-01-02 | MapReduce job completion time for datasets under 100 MB shall not exceed 5 minutes on the Docker-hosted Hadoop cluster. |
| NFR-01-03 | MongoDB queries executed against indexed fields shall return results within 500 milliseconds. |
| NFR-01-04 | The backend shall expose a `/health` endpoint returning the reachability status of MongoDB, the HDFS NameNode, and the YARN ResourceManager as three independent status fields: `{ "mongo": "ok|fail", "hdfs": "ok|fail", "yarn": "ok|fail" }`. |
| NFR-01-05 | The production React bundle size shall not exceed 2 MB gzipped. |

---

### NFR-02 — Data Security

| ID | Requirement |
|---|---|
| NFR-02-01 | JWT tokens shall be stored exclusively in httpOnly, SameSite=Strict cookies and shall never be accessible to client-side JavaScript. The frontend (port 5173) and backend (port 8000) share the same `localhost` registrable domain, so `SameSite=Strict` cookies are transmitted correctly without requiring `SameSite=None` or the `Secure` flag in local development. Developers must not change this to `SameSite=None` without also enforcing HTTPS, as `SameSite=None` requires the `Secure` attribute. |
| NFR-02-02 | All user input received at the API layer shall be validated and sanitized using Pydantic v2 models before being processed or stored. |
| NFR-02-03 | MongoDB connection credentials, JWT secrets, and all sensitive configuration values shall be stored in environment variables and never hardcoded in source files. |
| NFR-02-04 | CORS shall be configured with an explicit list of allowed origins. Wildcard origins shall not be permitted. |
| NFR-02-05 | Password values shall never appear in API responses, application logs, or error messages under any circumstances. |
| NFR-02-06 | All file upload operations shall validate file extension, MIME type, and file size before writing to HDFS. |
| NFR-02-07 | In the student deployment environment, all communication between the frontend, backend, and MongoDB occurs over localhost HTTP. For any production deployment, HTTPS must be enforced via a reverse proxy (e.g., Nginx with TLS termination) in front of the FastAPI process. The absence of TLS in the development scope is acknowledged and does not constitute a production-ready configuration. |
| NFR-02-08 | MongoDB encryption-at-rest is not configured in this student deployment. Enabling MongoDB Encrypted Storage Engine requires MongoDB Enterprise and is outside the scope of a local academic project. This is acknowledged as a gap relative to Doc 3 NFR requirements. In a production environment, encryption-at-rest must be enabled at the storage engine or disk level. |
| NFR-02-09 | The `/ingest/upload` and `/jobs/*` endpoints shall enforce a rate limit of 10 requests per minute per authenticated user, implemented via `slowapi`. Requests exceeding this limit shall receive HTTP 429. This prevents unintentional HDFS flooding during development iteration. |

---

### NFR-03 — Reliability

| ID | Requirement |
|---|---|
| NFR-03-01 | The Docker Compose configuration for the Hadoop cluster shall include health checks on the NameNode and DataNode containers. |
| NFR-03-02 | MongoDB data shall be stored on the host machine's native file system, ensuring data persistence is independent of any container lifecycle. |
| NFR-03-03 | HDFS data volumes within Docker Desktop shall be mapped to named Docker volumes to survive container restarts. |
| NFR-03-04 | The FastAPI backend shall handle MongoDB connection failures gracefully by returning HTTP 503 with a descriptive error rather than crashing. |
| NFR-03-05 | All asynchronous operations in the backend shall implement timeout handling and typed error fallback responses. |
| NFR-03-06 | A MongoDB backup script shall be provided at `backend/scripts/backup.sh`. The script shall invoke `mongodump --uri=$MONGO_URI --out=/backups/$(date +%F)` and is intended to be registered as a daily cron job on the host machine. Setup instructions including the cron entry (`0 2 * * * /path/to/backup.sh`) shall be documented in the repository `README.md`. This fulfills the Doc 3 requirement for regular automated data backups; full backup automation is the operator's responsibility in the production phase. |
| NFR-03-07 | The application targets 99% uptime as specified in the project requirements document. This SLA is not enforceable in the current student local deployment and is acknowledged as deferred to any future production phase. No uptime monitoring or SLA tooling is implemented at this stage. |

---

### NFR-04 — Scalability

| ID | Requirement |
|---|---|
| NFR-04-01 | The FastAPI backend shall be stateless (no in-process session storage) so that multiple instances can be run behind a load balancer in a future deployment. |
| NFR-04-02 | MongoDB collections shall be designed with shard key candidates documented in schema comments to support horizontal scaling if needed in the future. |
| NFR-04-03 | The Hadoop cluster defined in Docker Compose shall be extensible by adding additional DataNode service entries without modifying existing service definitions. |
| NFR-04-04 | All API list endpoints shall enforce pagination with a configurable page size (default: 50 records, maximum: 500 records per request). |

---

### NFR-05 — Performance Monitoring

| ID | Requirement |
|---|---|
| NFR-05-01 | The backend shall log all API requests using structured logging (Python `structlog`) including method, path, HTTP status code, and response duration. |
| NFR-05-02 | MapReduce job start time, end time, and duration in seconds shall be recorded in the `job_logs` MongoDB collection for historical performance tracking. |
| NFR-05-03 | The React frontend shall output page load time and API response durations to the browser console in development mode. |

---

### NFR-06 — Compliance and Standards

| ID | Requirement |
|---|---|
| NFR-06-01 | Climate data field naming in ingestion schemas shall follow World Meteorological Organization (WMO) standard naming conventions where applicable. |
| NFR-06-02 | The REST API shall follow standard conventions: resource-based URL structure, correct use of HTTP verbs (GET, POST, PATCH, DELETE), and semantically correct HTTP status codes. |
| NFR-06-03 | Python source code shall conform to PEP 8 style guidelines enforced via `ruff`. React and TypeScript code shall conform to the ESLint Airbnb configuration. |
| NFR-06-04 | All Docker images used in the Hadoop cluster shall be based on official, actively maintained base images. |

---

### NFR-07 — Documentation

| ID | Requirement |
|---|---|
| NFR-07-01 | The repository root `README.md` shall include: project overview, system architecture summary, hardware prerequisites, native setup steps for MongoDB and Python, Docker Desktop setup steps for Hadoop, a complete environment variable reference, and the cron-based backup setup instructions. |
| NFR-07-02 | The FastAPI backend shall expose auto-generated interactive API documentation via Swagger UI at `/docs` and ReDoc at `/redoc`. |
| NFR-07-03 | All machine learning model functions shall include docstrings describing the algorithm used, expected input format, and output structure. |
| NFR-07-04 | A video walkthrough shall be produced demonstrating the complete working system including: user login, file ingestion, MapReduce job execution, ML model training, dashboard visualization, and alert triggering. |
| NFR-07-05 | The frontend shall include a static `/help` page accessible to all authenticated users. The page shall cover the following topics as markdown-rendered content: how to log in and manage your session, how to upload a dataset and monitor ingestion status, how to trigger a MapReduce or ML job, how to configure alert rules and acknowledge events, and how to submit a support ticket. |

---

## 1.6 Hardware Prerequisites

The following hardware is required to run the full system locally, including the Docker-hosted Hadoop cluster:

| Component | Minimum | Recommended |
|---|---|---|
| CPU | Intel Core i5 (4 cores) | Intel Core i7 or equivalent (8 cores) |
| RAM | 16 GB | 32 GB |
| Storage | 500 GB SSD | 1 TB NVMe SSD |
| GPU | Not required for core system | Dedicated GPU optional for accelerated ML |
| OS | 64-bit Windows 10 or higher | Windows 11 64-bit |
| Docker Desktop RAM allocation | 4 GB minimum allocated to Docker Desktop | 8 GB |

**Note:** The Hadoop cluster running in Docker Desktop is the dominant resource consumer. Systems with less than 16 GB total RAM or fewer than 4 CPU cores will experience degraded MapReduce performance and potential NameNode instability. All demonstration datasets used in this project are kept under 50 MB to remain within these hardware constraints.

---

---

# PHASE 2 — SYSTEM DESIGN

## 2.1 High-Level Architecture

```
HOST MACHINE
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  ┌─────────────────┐   HTTP/REST    ┌───────────────────────────────────┐   │
│  │   React SPA     │ ─────────────▶ │         FastAPI Backend           │   │
│  │   (Vite)        │               │         (Python 3.13)             │   │
│  │   Port: 5173    │ ◀───────────── │                                   │   │
│  └─────────────────┘               │  Auth │ Ingest │ Jobs │ ML │ Alerts│   │
│                                    └──────────────┬────────────────────┘   │
│                                                   │                         │
│                                    ┌──────────────▼──────────────┐          │
│                                    │     MongoDB (native host)    │          │
│                                    │     Port: 27017              │          │
│                                    │                              │          │
│                                    │  users · climate_records     │          │
│                                    │  ingestion_logs · job_logs   │          │
│                                    │  ml_results · alert_rules    │          │
│                                    │  alert_events · tickets      │          │
│                                    │  revoked_tokens              │          │
│                                    └──────────────────────────────┘          │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Docker Desktop (Hadoop Cluster only)               │  │
│  │                                                                       │  │
│  │   ┌─────────────────────────┐    ┌──────────────────────────────┐   │  │
│  │   │   hadoop-namenode        │    │      hadoop-datanode          │   │  │
│  │   │   HDFS NameNode          │    │      HDFS DataNode            │   │  │
│  │   │   YARN ResourceManager   │    │      YARN NodeManager         │   │  │
│  │   │   Port: 9870 (Web UI)    │    │      Port: 9864 (Web UI)      │   │  │
│  │   │   Port: 8020 (IPC)       │    │                              │   │  │
│  │   │   Port: 8088 (YARN UI)   │    │                              │   │  │
│  │   └─────────────────────────┘    └──────────────────────────────┘   │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Key Design Decision:** MongoDB runs natively on the host machine to avoid Docker Desktop resource overhead and to provide reliable persistent storage without volume mapping complexity. Only the Hadoop cluster, which is inherently container-friendly and resource-isolated, runs inside Docker Desktop.

**Data Flow:**
1. User uploads a file → FastAPI validates schema and file hash → writes raw file to HDFS via WebHDFS REST API → logs ingestion metadata to MongoDB; the `ingestion_service.py` assigns the new `ingestion_log._id` as the `ingestion_id` field on every `climate_records` document parsed from that file before bulk-inserting them into MongoDB.
2. Admin or Analyst triggers a MapReduce job → FastAPI submits job to Hadoop via WebHDFS + YARN REST API → job reads from HDFS, writes output to HDFS → `job_service.py` polls YARN for application FINISHED state → reads `part-00000` from HDFS output path via WebHDFS → parses result lines → writes summary document to MongoDB `ml_results` and updates `job_logs` status to `completed`.
3. Analyst triggers ML training → FastAPI reads `climate_records` from MongoDB → trains model → `ml_service.py` stores predictions and metadata back to MongoDB → for anomaly detection, `ml_service.py` calls `climate_repo.bulk_update_anomaly_flags(record_ids)` to back-write `is_anomaly: true` on flagged records.
4. Frontend polls FastAPI → fetches aggregated data from MongoDB → renders charts and tables.
5. Background alert worker evaluates each new real-time record against active alert rules in MongoDB cache → writes triggered alert events → frontend notification panel polls for unacknowledged events; on any rule PATCH or DELETE, the cache is invalidated immediately.

---

## 2.2 Infrastructure Map

| Component | Runtime | Host / Port | Purpose |
|---|---|---|---|
| React Frontend | Native (Node 22, Vite) | `localhost:5173` | SPA served by Vite dev server |
| FastAPI Backend | Native (Python 3.13) | `localhost:8000` | REST API, job runner, ML engine |
| MongoDB | Native (MongoDB 7) | `localhost:27017` | Primary operational database |
| Hadoop NameNode | Docker Desktop | `localhost:9870`, `localhost:8020`, `localhost:8088` | HDFS metadata, YARN resource management |
| Hadoop DataNode | Docker Desktop | `localhost:9864` | HDFS block storage, job execution |

**Hadoop communication from FastAPI:** The backend communicates with HDFS using the WebHDFS REST API on port 9870 and submits MapReduce jobs via the YARN REST API on port 8088. No Hadoop client libraries need to be installed natively; all communication is over HTTP.

**HDFS security note:** The Docker Hadoop cluster runs in pseudo-distributed mode without Kerberos authentication. WebHDFS calls from `webhdfs.py` succeed without credentials. This is an accepted insecurity for local student scope. The HDFS WebHDFS port (9870) must not be exposed on any network interface other than localhost. This is documented in the README.

---

## 2.3 MongoDB Schema

### Collection: `users`
```
{
  _id:           ObjectId
  email:         String   (unique index)
  password_hash: String
  role:          String   enum["admin", "analyst", "viewer"]
  is_active:     Boolean
  created_at:    ISODate
  updated_at:    ISODate
}
```

### Collection: `climate_records`
```
{
  _id:              ObjectId
  source_type:      String   enum["satellite", "weather_station", "sensor"]
  location: {
    region:         String   (indexed)
    lat:            Float
    lon:            Float
  }
  timestamp:        ISODate  (indexed descending)
  temperature_c:    Float | null
  precipitation_mm: Float | null
  humidity_pct:     Float | null
  co2_ppm:          Float | null
  is_anomaly:       Boolean  (default: false)
  is_archived:      Boolean  (default: false)
  ingestion_id:     ObjectId (ref: ingestion_logs)
                             ← Set during ingestion: ingestion_service.py assigns the
                                parent ingestion_log._id to every record parsed from
                                that file before bulk-inserting to this collection.
  created_at:       ISODate
}

Indexes:
  { timestamp: -1 }
  { "location.region": 1, timestamp: -1 }
  { source_type: 1, timestamp: -1 }
  { is_anomaly: 1 }
  { is_archived: 1 }         ← Required to support default is_archived=false filter on GET /climate

Shard key candidate: { "location.region": 1, timestamp: -1 }
```

### Collection: `ingestion_logs`
```
{
  _id:           ObjectId
  filename:      String
  file_hash:     String   (unique index — SHA-256 for deduplication)
  hdfs_path:     String
  format:        String   enum["csv", "json", "geojson"]
  record_count:  Integer
  status:        String   enum["pending", "success", "failed"]
  error_message: String | null
  triggered_by:  ObjectId (ref: users)
  created_at:    ISODate
}
```

### Collection: `job_logs`
```
{
  _id:              ObjectId
  job_type:         String   enum["mapreduce", "ml_train"]
  job_name:         String
  status:           String   enum["queued", "running", "completed", "failed"]
  hdfs_input:       String | null   ← null for ml_train jobs; ML reads from MongoDB, not HDFS
  hdfs_output:      String | null   ← null for ml_train jobs; ML writes to MongoDB, not HDFS
  duration_seconds: Integer | null
  triggered_by:     ObjectId (ref: users)
  started_at:       ISODate
  completed_at:     ISODate | null
  error:            String | null
}

Indexes:
  { status: 1 }
  { triggered_by: 1, started_at: -1 }
```

### Collection: `ml_results`
```
{
  _id:                ObjectId
  model_type:         String   enum["anomaly_detection", "trend_prediction", "correlation"]
  trained_at:         ISODate
  record_count:       Integer
  accuracy_score:     Float | null
  predictions:        Array    ← Typed by model_type discriminator (see note below)
  anomaly_record_ids: Array[ObjectId]
  correlation_matrix: Object | null
  forecast_data:      Array | null
  job_id:             ObjectId (ref: job_logs)
}

predictions field structure by model_type:
  anomaly_detection  → Array[{ record_id: ObjectId, score: Float, is_anomaly: Boolean }]
  trend_prediction   → Array[{ region: String, date: ISODate, forecast_temp_c: Float }]
  correlation        → Not used; correlation data stored in correlation_matrix field instead

Indexes:
  { model_type: 1, trained_at: -1 }
```

### Collection: `alert_rules`
```
{
  _id:        ObjectId
  name:       String
  metric:     String  enum["temperature_c", "precipitation_mm", "co2_ppm", "humidity_pct"]
  operator:   String  enum[">", "<", "=", ">=", "<="]
  threshold:  Float
  severity:   String  enum["low", "medium", "high"]
  is_active:  Boolean
  created_by: ObjectId (ref: users)
  created_at: ISODate
}
```

### Collection: `alert_events`
```
{
  _id:                 ObjectId
  rule_id:             ObjectId (ref: alert_rules)
  climate_record_id:   ObjectId (ref: climate_records)
  triggered_value:     Float
  severity:            String
  acknowledged:        Boolean  (default: false)
  acknowledged_by:     ObjectId | null (ref: users)
  triggered_at:        ISODate
}

Indexes:
  { acknowledged: 1, triggered_at: -1 }
  { rule_id: 1 }
```

### Collection: `support_tickets`
```
{
  _id:            ObjectId
  subject:        String
  description:    String
  screenshot_url: String | null
  status:         String   enum["open", "in-progress", "resolved"]
  response:       String | null
  responded_by:   ObjectId | null (ref: users)   ← Attribution for admin response
  responded_at:   ISODate  | null                ← Timestamp of admin response
  submitted_by:   ObjectId (ref: users)
  created_at:     ISODate
  updated_at:     ISODate
}

Indexes:
  { submitted_by: 1, created_at: -1 }
  { status: 1 }
```

### Collection: `revoked_tokens`
```
{
  _id:        ObjectId
  jti:        String   (unique index)
  expires_at: ISODate  (TTL index: expireAfterSeconds: 0 — auto-deleted at expiry)
}
```

---

## 2.4 HDFS Directory Structure

```
/earthscape/
├── raw/
│   ├── satellite/
│   │   └── YYYY/MM/DD/<ingestion_id>.json
│   ├── weather_station/
│   │   └── YYYY/MM/DD/<ingestion_id>.csv
│   └── sensor/
│       └── YYYY/MM/DD/<ingestion_id>.json
│
├── processed/
│   └── mapreduce/
│       ├── temperature_agg/
│       │   └── <job_id>/part-00000
│       ├── precipitation_totals/
│       │   └── <job_id>/part-00000
│       └── anomaly_scores/
│           └── <job_id>/part-00000
│
└── tmp/
    └── <job_id>/     ← intermediate shuffle output, cleaned after job completion
```

All HDFS reads and writes from the FastAPI backend are performed via the **WebHDFS REST API** (HTTP on port 9870). No Hadoop client binary is required on the host. Files are streamed directly over HTTP using Python's `httpx` async client.

---

## 2.5 API Contract

**Base URL:** `http://localhost:8000/api/v1`
**Authentication:** JWT via httpOnly cookie named `access_token`
**Content-Type:** `application/json` for all request and response bodies unless stated otherwise

---

### Auth

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/auth/login` | Public | Submit email + password. On success, sets JWT cookie and returns user info. |
| POST | `/auth/logout` | Any authenticated | Adds current token jti to revoked_tokens. Clears cookie. |
| GET | `/auth/me` | Any authenticated | Returns current authenticated user's profile. |

---

### User Management

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/users` | Admin | Returns paginated list of all users. |
| POST | `/users` | Admin | Creates a new user with specified role. |
| PATCH | `/users/{id}` | Admin | Updates user role or active status. |
| DELETE | `/users/{id}` | Admin | Deactivates user account (soft delete via is_active: false). |

---

### Data Ingestion

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/ingest/upload` | Admin, Analyst | Accepts multipart file upload. Validates, hashes, writes to HDFS, logs to MongoDB. Returns ingestion log ID. Rate-limited: 10 req/min per user. |
| GET | `/ingest/logs` | Admin, Analyst | Returns paginated ingestion log list with status and record counts. |
| GET | `/ingest/logs/{id}` | Admin, Analyst | Returns full detail of a single ingestion log entry. |

---

### Jobs (MapReduce + ML)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/jobs/mapreduce` | Admin, Analyst | Triggers a MapReduce job. Request body: job_name, hdfs_input_path, job_type (temperature_agg, precipitation_totals, anomaly_scores). Rate-limited: 10 req/min per user. |
| POST | `/jobs/ml/train` | Admin, Analyst | Triggers ML model training. Request body: model_type (anomaly_detection, trend_prediction, correlation). Rate-limited: 10 req/min per user. |
| GET | `/jobs` | Admin, Analyst | Returns paginated list of all job logs with status. |
| GET | `/jobs/{id}` | Admin, Analyst | Returns full detail of a single job log including output path and error if failed. |

---

### Climate Data

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/climate` | Any authenticated | Returns paginated climate records. Query params: `region`, `source_type`, `from_date`, `to_date`, `is_anomaly`, `is_archived` (default: false), `page`, `limit`. The `is_archived` filter defaults to `false`; archived records are excluded from all queries unless `is_archived=true` is explicitly passed. |
| GET | `/climate/summary` | Any authenticated | Returns aggregated statistics per region and time period for dashboard rendering. |
| GET | `/climate/realtime` | Any authenticated | Returns the most recent N records tagged source_type: sensor. Default N: 100. |
| GET | `/climate/export` | Admin, Analyst | Returns currently filtered records as a downloadable CSV file. Same query params as `/climate`. Hard cap: 10,000 records. Returns HTTP 400 if the active filter resolves to more records than the cap. |

---

### Alerts

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/alerts/rules` | Any authenticated | Returns list of all alert rules. |
| POST | `/alerts/rules` | Admin | Creates a new alert rule. |
| PATCH | `/alerts/rules/{id}` | Admin | Updates threshold, operator, severity, or active status of a rule. Invalidates the in-memory alert cache immediately upon success. |
| DELETE | `/alerts/rules/{id}` | Admin | Deletes an alert rule. Invalidates the in-memory alert cache immediately upon success. |
| GET | `/alerts/events` | Any authenticated | Returns paginated alert events. Query param: acknowledged (true/false). |
| PATCH | `/alerts/events/{id}/acknowledge` | Any authenticated | Marks a specific alert event as acknowledged. |

---

### Support

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/support/tickets` | Any authenticated | Submits a new support ticket. |
| GET | `/support/tickets` | Any authenticated | Returns own tickets. Admins see all tickets. Paginated. |
| GET | `/support/tickets/{id}` | Any authenticated | Returns full ticket detail including admin response, responded_by, and responded_at if present. |
| PATCH | `/support/tickets/{id}` | Admin | Updates ticket status and adds written response. Records responded_by (admin user ID) and responded_at (current timestamp). |

---

### System

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/health` | Public | Returns reachability status of MongoDB, HDFS NameNode, and YARN ResourceManager as `{ "mongo": "ok|fail", "hdfs": "ok|fail", "yarn": "ok|fail" }`. |
| GET | `/metrics` | Admin | Returns request counters, job counts by status, and active alert rule count. |

---

## 2.6 UI Flow

```
[/login]  (public)
    │
    ▼ successful auth
[/dashboard]  ──────────────────── shared by all roles ────────────────────────
    │
    ├── Temperature Trend Line Chart (with ML forecast overlay if available)
    ├── Precipitation Bar Chart (monthly totals by region)
    ├── Anomaly Scatter Plot (flagged records highlighted in distinct color)
    ├── Correlation Heatmap (temperature / CO2 / precipitation / humidity)
    ├── Real-time Feed Panel (latest sensor records, polls every VITE_POLL_REALTIME_MS)
    └── Notifications Panel (unacknowledged alerts, polls every VITE_POLL_ALERTS_MS)

[Sidebar Navigation]
    │
    ├──▶ [/ingest]  (Admin, Analyst only)
    │        ├── Drag-and-drop or browse file upload
    │        ├── Format selector (CSV / JSON / GeoJSON)
    │        ├── Upload progress feedback
    │        └── Ingestion log table (status, record count, HDFS path)
    │
    ├──▶ [/jobs]  (Admin, Analyst only)
    │        ├── Trigger MapReduce Job form (job type + HDFS input path)
    │        ├── Trigger ML Training form (model type selector)
    │        └── Job list table (name, type, status, duration, triggered by)
    │            (polls every VITE_POLL_JOBS_MS)
    │
    ├──▶ [/climate]  (all authenticated users)
    │        ├── Filter bar: region, source type, date range, anomaly flag, archived flag
    │        ├── Paginated data table with all climate record fields
    │        └── Export to CSV button (Admin, Analyst only — capped at 10,000 records)
    │
    ├──▶ [/alerts]  (Admin only)
    │        ├── Alert rule list with create / edit / delete
    │        └── Alert events log with acknowledge action
    │
    ├──▶ [/users]  (Admin only)
    │        ├── User table with role and active status
    │        └── Create user form, deactivate toggle
    │
    ├──▶ [/support]  (all authenticated users)
    │        ├── Submit ticket form
    │        └── Ticket list with status badges and admin responses
    │
    └──▶ [/help]  (all authenticated users)
             └── Static markdown-rendered user guide covering: login/session,
                 data upload and ingestion monitoring, triggering jobs,
                 configuring and acknowledging alerts, submitting support tickets

Route Protection:
  /login                          → public
  /health                         → public
  /dashboard, /climate, /support,
  /help                           → any authenticated role
  /ingest, /jobs                  → Analyst or Admin only
  /alerts, /users                 → Admin only
  All other paths                 → redirect to /login
```

---

## 2.7 Backend Layer Structure

```
backend/
├── pyproject.toml
├── .env.example
├── scripts/
│   ├── producer.py              ← Synthetic sensor data producer; posts JSON records to
│   │                               /api/v1/ingest/upload at REALTIME_PRODUCER_INTERVAL.
│   │                               Configurable via CLI args or environment variable.
│   └── backup.sh                ← mongodump backup script; intended to run via daily cron:
│                                   0 2 * * * /path/to/backup.sh
│                                   Outputs to /backups/YYYY-MM-DD/
├── app/
│   ├── main.py                  ← FastAPI app instantiation, middleware registration,
│   │                               router mounting, lifespan startup/shutdown.
│   │                               Lifespan: connect Motor client, run create_indexes(),
│   │                               disconnect on shutdown.
│   ├── config.py                ← pydantic-settings Settings class; validated at startup,
│   │                               fail-fast on missing required vars.
│   ├── db/
│   │   └── mongo.py             ← Motor async client singleton; connect/disconnect lifecycle.
│   │                               create_indexes() called in lifespan — creates all
│   │                               collection indexes programmatically on first startup.
│   ├── models/                  ← Pydantic v2 request and response schemas, one file per domain
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── climate.py
│   │   ├── ingestion.py
│   │   ├── job.py
│   │   ├── ml.py
│   │   ├── alert.py
│   │   └── support.py
│   ├── repositories/            ← All MongoDB queries live here; no business logic
│   │   ├── user_repo.py
│   │   ├── climate_repo.py      ← Includes bulk_update_anomaly_flags(record_ids) method
│   │   ├── ingestion_repo.py
│   │   ├── job_repo.py
│   │   ├── ml_repo.py
│   │   ├── alert_repo.py
│   │   └── support_repo.py
│   ├── services/                ← Business logic; calls repositories; no DB access directly
│   │   ├── auth_service.py
│   │   ├── ingestion_service.py ← Assigns ingestion_id to each parsed record before insert
│   │   ├── job_service.py       ← Polls YARN → reads HDFS output → writes MongoDB summary
│   │   ├── ml_service.py        ← Trains models → calls climate_repo.bulk_update_anomaly_flags()
│   │   ├── alert_service.py     ← Manages cache; invalidates on rule PATCH/DELETE
│   │   └── support_service.py
│   ├── routes/                  ← FastAPI routers; no logic; call services only
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── ingest.py
│   │   ├── jobs.py
│   │   ├── climate.py
│   │   ├── alerts.py
│   │   ├── support.py
│   │   └── system.py
│   ├── middleware/
│   │   ├── auth.py              ← JWT verification FastAPI dependency; checks revocation list
│   │   └── logging.py           ← Structured request/response logger using structlog
│   ├── hadoop/
│   │   ├── webhdfs.py           ← WebHDFS REST API client (httpx async); upload, read, mkdir
│   │   └── yarn.py              ← YARN REST API client; submit job, poll application status
│   ├── jobs/
│   │   ├── mapreduce_runner.py  ← Assembles YARN Streaming job submission payload (see 2.16),
│   │   │                           streams output, calls job_service on completion
│   │   └── alert_worker.py      ← FastAPI BackgroundTask; evaluates rules on each new record;
│   │                               reads from in-memory cache; invalidated by alert_service
│   └── ml/
│       ├── anomaly.py           ← Isolation Forest training and prediction (scikit-learn)
│       ├── trend.py             ← Linear Regression 30-day forecast per region
│       └── correlation.py       ← Pearson correlation matrix across climate metrics
│
└── mapreduce/                   ← Python Hadoop Streaming scripts (copied to HDFS before job)
    ├── temperature_agg/
    │   ├── mapper.py
    │   └── reducer.py
    ├── precipitation_totals/
    │   ├── mapper.py
    │   └── reducer.py
    └── anomaly_scores/
        ├── mapper.py
        └── reducer.py
```

**Layer rules:**
- Routes call services only. Zero business logic in route handlers.
- Services call repositories only. Zero direct pymongo/motor calls in service layer.
- Repositories contain all MongoDB queries. Zero business logic.
- ML scripts are standalone modules. Called by services, return plain Python data structures.
- Hadoop clients (`webhdfs.py`, `yarn.py`) are pure HTTP clients. Called by services.
- Index creation lives exclusively in `db/mongo.py` `create_indexes()`. No DDL elsewhere.

---

## 2.8 Frontend Feature Structure

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── .env.example
└── src/
    ├── main.tsx
    ├── App.tsx                       ← Router setup, protected route wrapper
    ├── styles/
    │   └── theme.ts                  ← Single source of truth for all design tokens:
    │                                    colors, font sizes, spacing scale, border radius,
    │                                    chart palette. Zero hardcoded values elsewhere.
    ├── types/                        ← TypeScript interfaces matching backend Pydantic schemas
    │   ├── auth.ts
    │   ├── climate.ts
    │   ├── job.ts
    │   ├── alert.ts
    │   └── support.ts
    ├── services/
    │   └── api.ts                    ← Axios instance with base URL, cookie credentials,
    │                                    request interceptor for error normalization
    ├── stores/                       ← Zustand stores for cross-feature state
    │   ├── authStore.ts              ← Current user, login/logout actions
    │   ├── alertStore.ts             ← Unacknowledged alert count, notification list
    │   └── jobStore.ts               ← Active job statuses for polling
    ├── hooks/
    │   ├── useAuth.ts                ← Reads authStore, provides role checks
    │   ├── usePoll.ts                ← Generic polling hook with configurable interval;
    │   │                                interval sourced from env vars, never hardcoded
    │   └── useToast.ts               ← Toast notification trigger
    ├── components/                   ← Shared, stateless UI primitives
    │   ├── Button.tsx
    │   ├── Table.tsx
    │   ├── Modal.tsx
    │   ├── Badge.tsx
    │   ├── Spinner.tsx
    │   ├── FilterBar.tsx
    │   └── Pagination.tsx
    └── features/
        ├── auth/
        │   ├── LoginPage.tsx
        │   └── ProtectedRoute.tsx
        ├── dashboard/
        │   ├── DashboardPage.tsx
        │   ├── TemperatureTrendChart.tsx
        │   ├── PrecipitationChart.tsx
        │   ├── AnomalyScatterPlot.tsx
        │   ├── CorrelationHeatmap.tsx
        │   ├── RealtimeFeedPanel.tsx
        │   └── NotificationsPanel.tsx
        ├── ingestion/
        │   ├── IngestionPage.tsx
        │   ├── FileUploadZone.tsx
        │   └── IngestionLogTable.tsx
        ├── jobs/
        │   ├── JobsPage.tsx
        │   ├── MapReduceJobForm.tsx
        │   ├── MLTrainForm.tsx
        │   └── JobStatusList.tsx
        ├── climate/
        │   ├── ClimateExplorerPage.tsx
        │   ├── ClimateTable.tsx
        │   └── ExportButton.tsx
        ├── alerts/
        │   ├── AlertsPage.tsx
        │   ├── AlertRuleForm.tsx
        │   ├── AlertRuleList.tsx
        │   └── AlertEventLog.tsx
        ├── users/
        │   ├── UsersPage.tsx
        │   ├── UserTable.tsx
        │   └── CreateUserForm.tsx
        ├── support/
        │   ├── SupportPage.tsx
        │   ├── TicketForm.tsx
        │   └── TicketList.tsx
        └── help/
            └── HelpPage.tsx          ← Static markdown-rendered user guide (see NFR-07-05)
```

**Component rules:**
- Zero business logic in component files. All data fetching and state lives in hooks or stores.
- Components receive data via props or read from stores. No direct API calls inside JSX.
- All chart components read from a common `useDashboardData` hook that handles polling.
- All polling intervals are read from `import.meta.env.VITE_POLL_*` variables; no hardcoded millisecond values in component or hook files.

---

## 2.9 MapReduce Job Design

### Job 1: Temperature Aggregation
- **Purpose:** Compute minimum, maximum, and mean temperature per geographic region from raw weather station CSV files stored in HDFS.
- **Input format:** CSV with columns `region, timestamp, temperature_c, ...`
- **Mapper:** Reads each line, parses region and temperature_c, skips null/empty temperature values, emits tab-separated pair `region \t temperature_c`
- **Reducer:** Collects all temperature values per region, computes min, max, and mean, emits `region \t min \t max \t mean`
- **Output path:** `/earthscape/processed/mapreduce/temperature_agg/<job_id>/`

### Job 2: Precipitation Totals
- **Purpose:** Compute total monthly precipitation per region for trend and historical analysis.
- **Input format:** CSV with columns `region, timestamp, precipitation_mm, ...`
- **Mapper:** Extracts region and YYYY-MM from timestamp, emits `region_YYYY-MM \t precipitation_mm`; skips null values
- **Reducer:** Sums all precipitation values per composite key, emits `region_YYYY-MM \t total_mm`
- **Output path:** `/earthscape/processed/mapreduce/precipitation_totals/<job_id>/`

### Job 3: Anomaly Scoring
- **Purpose:** Assign a Z-score-based anomaly score to each sensor record per region and flag records where any metric deviates beyond a threshold of 2.5 standard deviations.
- **Input format:** JSON lines with fields `record_id, region, temperature_c, humidity_pct, co2_ppm`
- **Mapper:** Emits `region \t json_record_string` for each record
- **Reducer:** Groups records by region, computes mean and standard deviation per metric across the group, calculates per-record Z-score, sets `is_anomaly: true` if any metric |Z| > 2.5, emits JSON object per record with `record_id, anomaly_score, is_anomaly`
- **Output path:** `/earthscape/processed/mapreduce/anomaly_scores/<job_id>/`

**Execution mechanism:** All three jobs are submitted as Hadoop Streaming jobs via the YARN REST API. The Python mapper and reducer scripts are first uploaded to HDFS by the FastAPI backend using WebHDFS. The job submission payload structure is defined in section 2.16. FastAPI polls the YARN application status API until the job reaches FINISHED or FAILED state, then `job_service.py` reads the `part-00000` output from HDFS via WebHDFS, parses result lines, writes a summary document to MongoDB, and updates the `job_logs` document status accordingly.

---

## 2.10 Machine Learning Model Design

| Model | Algorithm | Training Data Source | Output Stored in MongoDB |
|---|---|---|---|
| Anomaly Detection | Isolation Forest (scikit-learn) | `climate_records` — last 90 days, fields: temperature_c, precipitation_mm | `ml_results.predictions`: `Array[{ record_id, score, is_anomaly }]`; `ml_service.py` then calls `climate_repo.bulk_update_anomaly_flags()` to back-write `is_anomaly: true` on flagged `climate_records` documents |
| Trend Prediction | Linear Regression (scikit-learn) | Daily mean temperature per region from `climate_records` — last 365 days | `ml_results.forecast_data`: `Array[{ region, date, forecast_temp_c }]` — 30 elements per region |
| Correlation Analysis | Pearson correlation (pandas / numpy) | All fields: temperature_c, co2_ppm, precipitation_mm, humidity_pct from `climate_records` | `ml_results.correlation_matrix`: 4×4 JSON object keyed by metric name; `predictions` field is an empty array for this model type |

All models are trained entirely within the FastAPI backend process using scikit-learn and pandas. No external ML infrastructure is required. Training is triggered on demand via the `/jobs/ml/train` endpoint.

---

## 2.11 Alert Engine Design

The alert engine runs as a FastAPI `BackgroundTask` that is invoked automatically each time a new real-time climate record is written to MongoDB via the ingestion endpoint.

**Execution flow:**
1. New sensor record inserted to `climate_records`
2. Background task starts asynchronously
3. Active `alert_rules` are loaded from an in-memory cache (TTL controlled by `ALERT_CACHE_TTL_SECONDS`; also invalidated immediately whenever a rule is created, modified, or deleted via the API)
4. Each active rule is evaluated against the incoming record's matching metric field
5. If the rule condition evaluates to true, an `alert_event` document is inserted to MongoDB with the rule ID, record ID, actual value, severity, and current timestamp
6. Frontend notification panel polls `/alerts/events?acknowledged=false` every `VITE_POLL_ALERTS_MS` milliseconds and displays all unacknowledged events

**Cache invalidation:** The `alert_service.py` exposes an `invalidate_cache()` method. The `PATCH /alerts/rules/{id}` and `DELETE /alerts/rules/{id}` route handlers call this method on every successful rule mutation. This ensures a deactivated or deleted rule stops firing on the very next ingested record rather than remaining active until the next TTL cycle.

**Email simulation:** When an alert fires, the backend logs a structured notification payload (including rule name, triggered value, and severity) using `structlog` and writes a `notification_log` field to the alert event document. No actual email is sent in the student scope.

---

## 2.12 Environment Variables

### Backend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `MONGO_URI` | MongoDB connection string (native host) | `mongodb://localhost:27017` |
| `MONGO_DB` | Database name | `earthscape` |
| `JWT_SECRET` | JWT signing secret — minimum 32 characters | `change-me-to-a-random-secret` |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes | `60` |
| `HDFS_NAMENODE_HOST` | Hadoop NameNode hostname | `localhost` |
| `HDFS_WEBHDFS_PORT` | WebHDFS HTTP port | `9870` |
| `YARN_RM_PORT` | YARN ResourceManager REST API port | `8088` |
| `HADOOP_STREAMING_JAR` | HDFS path to hadoop-streaming jar | `/usr/local/hadoop/share/hadoop/tools/lib/hadoop-streaming-3.3.6.jar` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `ALERT_CACHE_TTL_SECONDS` | Alert rule in-memory cache refresh interval | `60` |
| `REALTIME_PRODUCER_INTERVAL` | Seconds between synthetic data events (used by producer.py) | `10` |

### Frontend (`.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | FastAPI base URL for axios client | `http://localhost:8000/api/v1` |
| `VITE_POLL_REALTIME_MS` | Polling interval for the real-time feed panel in milliseconds | `10000` |
| `VITE_POLL_ALERTS_MS` | Polling interval for the notifications panel in milliseconds | `15000` |
| `VITE_POLL_JOBS_MS` | Polling interval for the job status list in milliseconds | `5000` |

All `VITE_POLL_*` values are read exclusively from these environment variables. No polling interval is hardcoded anywhere in the frontend component or hook source files.

---

## 2.13 Docker Compose Specification (Hadoop Cluster Only)

```
Services defined in docker-compose.yml:

hadoop-namenode:
  image: apache/hadoop:3.3.6
  ports:
    - "9870:9870"   ← WebHDFS + NameNode Web UI
    - "8020:8020"   ← HDFS IPC (used by DataNode and Streaming jobs)
    - "8088:8088"   ← YARN ResourceManager Web UI + REST API
  volumes:
    - hadoop_namenode_data:/hadoop/dfs/name
  environment:
    CLUSTER_NAME: earthscape
  networks:
    - hadoop-net
  healthcheck:
    test: curl -f http://localhost:9870 || exit 1
    interval: 30s
    retries: 5

hadoop-datanode:
  image: apache/hadoop:3.3.6
  depends_on:
    hadoop-namenode:
      condition: service_healthy
  ports:
    - "9864:9864"   ← DataNode Web UI
  volumes:
    - hadoop_datanode_data:/hadoop/dfs/data
  environment:
    SERVICE_PRECONDITION: "hadoop-namenode:9870"
  networks:
    - hadoop-net

volumes:
  hadoop_namenode_data:
  hadoop_datanode_data:

networks:
  hadoop-net:
    driver: bridge
```

The FastAPI backend communicates with the NameNode via `http://localhost:9870` (WebHDFS) and `http://localhost:8088` (YARN). Both ports are exposed to the host machine from the Docker network, so the native Python process can reach them directly without joining the Docker network.

---

## 2.14 Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Docker Desktop memory exhaustion running Hadoop on low-spec hardware | High | Allocate minimum 4 GB RAM to Docker Desktop; use small synthetic datasets (< 50 MB) for all demonstrations; run single DataNode only |
| WebHDFS connection refused when NameNode container is starting | Medium | FastAPI `/health` endpoint checks NameNode reachability before accepting job requests; retry logic with exponential backoff in `webhdfs.py` |
| MongoDB not running natively when backend starts | Medium | Backend startup sequence checks MongoDB connection via Motor; logs actionable error and exits with non-zero code if unreachable |
| JWT secret accidentally committed to source control | Critical | `.env` listed in `.gitignore`; `.env.example` contains only placeholder strings; CI check fails on any `.env` file in commit |
| ML model accuracy poor on small student-scale datasets | Low | Student scope — accuracy is documented as illustrative; algorithm correctness and output structure are the graded criteria, not model performance metrics |
| Duplicate ingestion corrupting climate records | Medium | SHA-256 hash deduplication check in `ingestion_service.py` rejects file before any HDFS write occurs |
| YARN job submission failing due to missing streaming JAR path | Medium | `HADOOP_STREAMING_JAR` env var validated at startup via pydantic-settings; descriptive error returned if path is unreachable on HDFS |
| Alert cache serving deactivated/deleted rules for up to TTL seconds | Medium | `alert_service.py` calls `invalidate_cache()` on every successful rule PATCH or DELETE; cache is rebuilt on next record ingested. TTL serves only as a passive fallback, not the primary invalidation mechanism. |
| HDFS WebHDFS port exposed without authentication | Medium | Hadoop pseudo-distributed mode runs without Kerberos auth by default; all WebHDFS calls succeed without credentials. Port 9870 must be bound to `127.0.0.1` only and never exposed externally. Documented in README as an accepted local-scope insecurity. |
| CSV export OOM on large unfiltered datasets | High | Export endpoint enforces a hard cap of 10,000 records. Requests exceeding the cap receive HTTP 400 before any data is streamed. Documented in API contract. |

---

## 2.15 Test Data Strategy

All demonstration and development testing uses a fixed set of seed files included in the repository under `backend/seed_data/`. These files provide reproducible data for the demo video, MapReduce job execution, and ML model training.

### Seed Files

| File | Format | Records | Date Range | Regions | Purpose |
|---|---|---|---|---|---|
| `weather_stations_2023.csv` | CSV | 5,000 | 2023-01-01 to 2023-12-31 | Karachi, Lahore, Islamabad, Quetta, Peshawar | Temperature aggregation and precipitation MapReduce jobs |
| `sensor_realtime_sample.json` | JSON Lines | 500 | 2024-01-01 to 2024-03-31 | Karachi, Lahore | Anomaly scoring MapReduce job and ML anomaly detection |
| `satellite_metadata_q1_2024.json` | JSON | 200 | 2024-01-01 to 2024-03-31 | All regions | Ingestion format coverage |

### Field Structure

**`weather_stations_2023.csv` columns:**
```
region, timestamp (ISO 8601), temperature_c, precipitation_mm, humidity_pct, co2_ppm
```

**`sensor_realtime_sample.json` fields per record:**
```json
{
  "record_id": "string (UUID)",
  "region": "string",
  "timestamp": "ISO 8601",
  "temperature_c": "float",
  "humidity_pct": "float",
  "co2_ppm": "float",
  "precipitation_mm": "float"
}
```

### Synthetic Anomalies

Approximately 5% of records in `sensor_realtime_sample.json` contain deliberately injected anomalies (temperature values exceeding 3 standard deviations from the regional mean) to ensure the anomaly detection model produces visible output during the demonstration. Anomalous records are tagged with a comment field `"_injected_anomaly": true` for verification purposes; this field is stripped by the ingestion parser and is not written to MongoDB.

### Usage

Load seed data before recording the demo video:
```
cd backend
python scripts/seed.py --file seed_data/weather_stations_2023.csv
python scripts/seed.py --file seed_data/sensor_realtime_sample.json
python scripts/seed.py --file seed_data/satellite_metadata_q1_2024.json
```

---

## 2.16 YARN Streaming Job Submission Payload

Submitting a Hadoop Streaming job via the YARN REST API is a two-step process. `mapreduce_runner.py` in `app/jobs/` implements both steps.

### Step 1 — Obtain a New Application ID

```
POST http://localhost:8088/ws/v1/cluster/apps/new-application
```

Response: `{ "application-id": "application_<timestamp>_<seq>", "maximum-resource-capability": { ... } }`

Extract `application-id` for use in Step 2.

### Step 2 — Submit the Application

```
POST http://localhost:8088/ws/v1/cluster/apps
Content-Type: application/json
```

**Payload structure:**

```json
{
  "application-id": "<application-id from Step 1>",
  "application-name": "<job_name from request body>",
  "application-type": "MAPREDUCE",
  "am-container-spec": {
    "commands": {
      "command": "{{JAVA_HOME}}/bin/java -Xmx512m org.apache.hadoop.mapreduce.v2.app.MRAppMaster 1><LOG_DIR>/AppMaster.stdout 2><LOG_DIR>/AppMaster.stderr"
    },
    "environment": {
      "entry": [
        { "key": "CLASSPATH", "value": "{{CLASSPATH}}" },
        { "key": "JAVA_HOME",  "value": "{{JAVA_HOME}}" }
      ]
    },
    "local-resources": {
      "entry": [
        {
          "key": "mapper.py",
          "value": {
            "resource": "hdfs://localhost:8020/earthscape/scripts/<job_type>/mapper.py",
            "type": "FILE",
            "visibility": "APPLICATION",
            "size": "<file_size_bytes>",
            "timestamp": "<hdfs_modification_time_ms>"
          }
        },
        {
          "key": "reducer.py",
          "value": {
            "resource": "hdfs://localhost:8020/earthscape/scripts/<job_type>/reducer.py",
            "type": "FILE",
            "visibility": "APPLICATION",
            "size": "<file_size_bytes>",
            "timestamp": "<hdfs_modification_time_ms>"
          }
        },
        {
          "key": "hadoop-streaming.jar",
          "value": {
            "resource": "hdfs://localhost:8020<HADOOP_STREAMING_JAR env var value>",
            "type": "FILE",
            "visibility": "PUBLIC",
            "size": "<jar_size_bytes>",
            "timestamp": "<hdfs_modification_time_ms>"
          }
        }
      ]
    }
  },
  "resource": {
    "memory": 1024,
    "vCores": 1
  },
  "priority": { "priority": 1 },
  "queue": "default",
  "unmanaged-AM": false
}
```

**Notes on the payload:**

- `size` and `timestamp` values for each local resource must be fetched from HDFS using a `GET` WebHDFS `GETFILESTATUS` call before building the submission payload. `mapreduce_runner.py` calls `webhdfs.get_file_status(path)` for each resource.
- The mapper and reducer scripts must be uploaded to `/earthscape/scripts/<job_type>/` on HDFS before Step 1 is executed. Upload is performed by `webhdfs.upload_file()` on every job submission to ensure the latest script version is used.
- The actual Streaming invocation (input path, output path, mapper, reducer) is passed via `mapreduce.job.reduces` and related properties in the `configuration` block, or more commonly by launching the Streaming JAR as the AM command with all `-input`, `-output`, `-mapper`, `-reducer` arguments inline. The simplified AM command shown above is a skeleton; the real command string in `mapreduce_runner.py` shall be:

```
hadoop jar hadoop-streaming.jar \
  -input  <hdfs_input_path> \
  -output /earthscape/processed/mapreduce/<job_type>/<job_id> \
  -mapper mapper.py \
  -reducer reducer.py \
  -file mapper.py \
  -file reducer.py
```

This command string is assembled dynamically by `mapreduce_runner.py` using the `job_id`, `job_type`, and `hdfs_input_path` values from the API request.

### Polling for Completion

After submission, `job_service.py` polls the following endpoint every 10 seconds:

```
GET http://localhost:8088/ws/v1/cluster/apps/<application-id>
```

The response `app.state` field progresses through: `NEW → ACCEPTED → RUNNING → FINISHED | FAILED | KILLED`.

When `state == FINISHED` and `finalStatus == SUCCEEDED`, `job_service.py` reads the output path from HDFS and writes the parsed summary to MongoDB. When `finalStatus == FAILED`, the `app.diagnostics` field is written to `job_logs.error`.

---

## 2.17 Data Flow Diagrams

### Level-0 Context DFD

```
                     ┌─────────────────────────────┐
                     │                             │
  Administrator ────▶│                             │────▶ Climate Reports
  Analyst       ────▶│   EarthScape Climate        │────▶ Job Status Updates
  Viewer        ────▶│   Analytics Platform        │────▶ Alert Notifications
                     │                             │────▶ ML Predictions
  External Data ────▶│                             │────▶ Exported CSV
  Sources            │                             │
  (CSV / JSON /      └─────────────────────────────┘
   GeoJSON uploads)
```

The system receives climate datasets and user commands; it produces analysis outputs, visualizations, and alert notifications.

---

### Level-1 DFD — Ingestion and Storage Flow

```
  User
   │
   │ Upload File (CSV/JSON/GeoJSON)
   ▼
┌──────────────────┐
│  1.0             │  validate schema,     ┌─────────────────┐
│  File Validation │ ──── compute hash ──▶ │  ingestion_logs │
│  & Dedup Check   │                       │  (MongoDB)      │
└──────────────────┘                       └─────────────────┘
   │ valid + unique file
   ▼
┌──────────────────┐
│  2.0             │  raw file bytes       ┌─────────────────┐
│  HDFS Write      │ ─────────────────────▶│  HDFS /raw/     │
│  (WebHDFS)       │                       │  (Docker)       │
└──────────────────┘                       └─────────────────┘
   │ HDFS path confirmed
   ▼
┌──────────────────┐
│  3.0             │  parsed records       ┌─────────────────┐
│  Record Parser   │ + ingestion_id ──────▶│ climate_records │
│  & MongoDB Write │                       │  (MongoDB)      │
└──────────────────┘                       └─────────────────┘
   │ insert complete
   ▼
┌──────────────────┐
│  4.0             │  evaluate each        ┌─────────────────┐
│  Alert Worker    │  record vs rules ────▶│  alert_events   │
│  (Background)    │                       │  (MongoDB)      │
└──────────────────┘                       └─────────────────┘
```

---

### Level-1 DFD — MapReduce Processing Flow

```
  Analyst / Admin
   │
   │ POST /jobs/mapreduce { job_type, hdfs_input_path }
   ▼
┌──────────────────┐
│  1.0             │  upload scripts       ┌─────────────────┐
│  Script Upload   │ ─────────────────────▶│ HDFS /scripts/  │
│  (WebHDFS)       │                       │  (Docker)       │
└──────────────────┘                       └─────────────────┘
   │ scripts on HDFS
   ▼
┌──────────────────┐
│  2.0             │  YARN REST submit     ┌─────────────────┐
│  Job Submission  │ ─────────────────────▶│ YARN Resource   │
│  (YARN REST API) │                       │ Manager         │
└──────────────────┘                       │  (Docker)       │
   │ application-id                        └─────────────────┘
   ▼                                              │ schedules
┌──────────────────┐                              ▼
│  3.0             │◀── poll state ──────  ┌─────────────────┐
│  Status Polling  │                       │ YARN NodeManager│
│  (job_service)   │   reads HDFS input,   │ executes        │
└──────────────────┘   writes HDFS output  │ mapper/reducer  │
   │ FINISHED                              └─────────────────┘
   ▼                                              │ output written
┌──────────────────┐  reads part-00000     ┌─────────────────┐
│  4.0             │ ◀──────────────────── │ HDFS /processed/│
│  Result Writer   │                       │  (Docker)       │
│  (job_service)   │                       └─────────────────┘
└──────────────────┘
   │ parsed summary
   ▼
┌─────────────────┐
│  ml_results /   │
│  job_logs       │
│  (MongoDB)      │
└─────────────────┘
```

---

### Flowchart — Alert Evaluation Loop

```
New climate record written to climate_records
              │
              ▼
    ┌──────────────────┐
    │ Load alert rules │◀────── cache hit? ──── in-memory cache (TTL or invalidated)
    │ from cache       │
    └──────────────────┘
              │
              ▼
    ┌──────────────────┐
    │  rules list      │
    │  empty?          │──── YES ──▶ END
    └──────────────────┘
              │ NO
              ▼
    ┌──────────────────┐
    │  take next rule  │
    └──────────────────┘
              │
              ▼
    ┌──────────────────────────────┐
    │  rule.metric field exists    │
    │  on this record?             │──── NO ──▶ skip rule
    └──────────────────────────────┘
              │ YES
              ▼
    ┌──────────────────────────────┐
    │  evaluate:                   │
    │  record[metric] <operator>   │
    │  rule.threshold              │──── FALSE ──▶ skip rule
    └──────────────────────────────┘
              │ TRUE
              ▼
    ┌──────────────────────────────┐
    │  insert alert_event to       │
    │  MongoDB (rule_id, record_id,│
    │  triggered_value, severity,  │
    │  acknowledged: false)        │
    └──────────────────────────────┘
              │
              ▼
    ┌──────────────────────────────┐
    │  log notification payload    │
    │  via structlog               │
    └──────────────────────────────┘
              │
              ▼
    ┌──────────────────┐
    │  more rules?     │──── YES ──▶ take next rule
    └──────────────────┘
              │ NO
              ▼
             END
```