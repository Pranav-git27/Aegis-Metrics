

# 🛡️ Aegis Metrics

**DevSecOps Telemetry & Threat-Triage Platform for Smart-City Infrastructure**

Aegis Metrics is an end-to-end security monitoring system that generates synthetic municipal system request logs, streams them into a cloud database, triages anomalies into actionable security alerts, and visualizes everything on a real-time dashboard.

**Key capabilities:**

- 🔄 Continuous synthetic telemetry generation with anomaly injection
- ⚡ Relational threat triage — anomalies escalate instantly to security alerts
- 📊 Aggregated dashboard metrics via a PostgreSQL view
- 🖥️ Real-time React dashboard with auto-polling, KPI cards, and an active threat feed
- ✅ One-click alert resolution with optimistic UI updates

---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Quick Start](#quick-start)
  - [1. Data Pipeline (Ingestion)](#1-data-pipeline-ingestion)
  - [2. Backend API Server](#2-backend-api-server)
  - [3. Frontend Dashboard](#3-frontend-dashboard)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Development Roadmap](#development-roadmap)
- [Repository Hygiene](#repository-hygiene)

---

## Overview

Aegis Metrics simulates a smart-city security operations center. Synthetic request logs are generated for municipal systems (traffic-light nodes, water pumps, street-light hubs), ingested into a Supabase (PostgreSQL) database, and continuously evaluated for anomalies. High-risk traffic is escalated into `security_alerts` with relational UUID tracking, while a FastAPI backend exposes aggregated analytics and a React frontend renders a live threat-triage dashboard.

**Key capabilities:**

- 🔄 Continuous synthetic telemetry generation with anomaly injection
- ⚡ Relational threat triage — anomalies escalate instantly to security alerts
- 📊 Aggregated dashboard metrics via a PostgreSQL view
- 🖥️ Real-time React dashboard with auto-polling, KPI cards, and an active threat feed
- ✅ One-click alert resolution with optimistic UI updates

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  data_pipeline  │────▶│     Supabase     │◀────│    backend      │
│  (generator +   │     │   (PostgreSQL)   │     │  (FastAPI API)  │
│   orchestrator) │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                        • system_logs                     │
                        • security_alerts                 │ REST
                        • dashboard_metrics (view)        ▼
                                               ┌─────────────────┐
                                               │    frontend     │
                                               │  (React + Vite) │
                                               └─────────────────┘
```

- **Data Pipeline** — Generates batches of synthetic logs and streams them to Supabase every few seconds, conditionally escalating `medium`/`high`/`critical` anomalies into security alerts.
- **Backend** — A FastAPI service that queries Supabase for aggregated overview metrics and active alerts, and exposes alert-resolution endpoints.
- **Frontend** — A Vite + React + Tailwind dashboard that polls the backend on a 4-second cadence and renders KPI cards plus a live threat feed.

---

## Project Structure

```
Aegis Metrics/
├── backend/
│   ├── api_server.py                  # FastAPI application & REST endpoints
│   ├── supabase_client.py             # Supabase client + DB insert/trigger helpers
│   ├── schema.sql                     # system_logs & security_alerts table DDL
│   └── migrations/
│       └── dashboard_metrics_view.sql # Aggregated metrics VIEW
├── data_pipeline/
│   ├── generator.py                   # Synthetic smart-city log generator
│   ├── orchestrator.py                # Continuous ingestion + alert escalation loop
│   ├── bulk_injector.py               # Stage 4 bulk array-batch injector (15k logs + lateral movement)
│   └── gnn_extractor.py               # Stage 4 GNN dataset extractor (graph + node features)
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx                   # React entry point
│       ├── App.jsx                    # Dashboard shell, polling & state
│       ├── api.js                     # Centralized API client
│       ├── KpiCard.jsx                # Reusable KPI metric card
│       └── AlertsTable.jsx            # Active threat feed table
├── models/
│   └── dataset/                       # Stage 4 GNN training artifacts (Colab-ready)
│       ├── graph.json                 # Full graph payload (index map, edge_index, features)
│       ├── node_features.csv          # N x 4 per-device feature matrix
│       └── edge_index.csv             # Directed edge list (COO source,target pairs)
├── requirements.txt                   # Python dependencies
└── README.md
```

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.9 | Data pipeline & backend |
| Node.js | ≥ 18 | Frontend build tooling |
| npm | ≥ 9 | Frontend package management |
| Supabase account | — | Hosted PostgreSQL database |

---

## Environment Configuration

The backend and pipeline read Supabase credentials from a local `.env` file. Create one in the project root:

```bash
# .env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-anon-key
```

> **Note:** If `SUPABASE_URL` or `SUPABASE_KEY` are missing (or the `supabase` package isn't installed), the backend and pipeline automatically fall back to a **mock/development mode** that returns zeroed metrics and generated UUIDs. This lets you run the stack locally without a live database.

---

## Database Setup

Apply the schema and the metrics view against your Supabase (PostgreSQL) database. Run the SQL in the Supabase SQL Editor or via `psql`:

1. **Create the tables** ([`backend/schema.sql`](backend/schema.sql)):

   ```sql
   -- system_logs: raw request telemetry
   -- security_alerts: anomaly metadata linked to log records (FK → system_logs.id)
   ```

2. **Create the aggregated view** ([`backend/migrations/dashboard_metrics_view.sql`](backend/migrations/dashboard_metrics_view.sql)):

   ```sql
   -- dashboard_metrics: single-row view with total_logs, total_alerts,
   -- anomaly_rate_percentage, and critical_alerts_count
   ```

---

## Quick Start

Run the three components in separate terminals. The recommended order is **Pipeline → Backend → Frontend**.

### 1. Data Pipeline (Ingestion)

Installs Python dependencies and starts the continuous ingestion loop that streams synthetic logs to Supabase and escalates anomalies.

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the continuous ingestion pipeline (2s interval by default)
python data_pipeline/orchestrator.py
```

To generate a one-off batch of synthetic logs without writing to the database:

```bash
python data_pipeline/generator.py
```

> Press `Ctrl+C` to stop the orchestrator gracefully (it handles `KeyboardInterrupt` cleanly).

---

### 2. Backend API Server

Starts the FastAPI service on `http://localhost:8000`.

```bash
# From the project root
python backend/api_server.py
```

The API will be available at:

- **Base URL:** `http://localhost:8000`
- **Interactive docs (Swagger UI):** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/`

---

### 3. Frontend Dashboard

Installs Node dependencies and launches the Vite dev server on `http://localhost:5173`.

```bash
# Install frontend dependencies
cd frontend
npm install

# Start the development server (opens browser automatically)
npm run dev
```

Additional frontend scripts:

| Command | Description |
|---------|-------------|
| `npm run dev` | Start the Vite dev server (port 5173) |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |

> The frontend expects the backend to be running on `http://localhost:8000` (configured in [`frontend/src/api.js`](frontend/src/api.js)). CORS is pre-configured to allow the Vite dev origin.

---

## API Reference

All endpoints are prefixed under `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns service status |
| `GET` | `/api/v1/analytics/overview` | Aggregated dashboard metrics (totals, anomaly rate, critical count) |
| `GET` | `/api/v1/alerts/active` | All unresolved alerts, sorted by `anomaly_score` descending |
| `PUT` | `/api/v1/alerts/{alert_id}/resolve` | Mark a single alert as resolved |

**Example — Overview response:**

```json
{
  "total_logs": 12480,
  "total_alerts": 612,
  "anomaly_rate_percentage": 4.91,
  "critical_alerts_count": 18
}
```

**Example — Active alert object:**

```json
{
  "alert_id": "a1b2c3d4-...",
  "log_id": "e5f6g7h8-...",
  "anomaly_score": 0.87,
  "model_source": "brute_force_model",
  "risk_level": "high",
  "is_resolved": false
}
```

---

## Data Model

### `system_logs`

Raw request telemetry for municipal systems.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID (PK) | Auto-generated |
| `timestamp` | TIMESTAMPTZ | Defaults to `now()` |
| `device_id` | TEXT | e.g. `TRAFFIC_LIGHT_NODE_04` |
| `request_method` | TEXT | `GET` / `POST` / `PUT` / `DELETE` |
| `endpoint` | TEXT | e.g. `/api/v1/telemetry` |
| `ip_address` | TEXT | Source IPv4 |
| `response_code` | INTEGER | HTTP status |
| `payload_size_bytes` | INTEGER | Request payload size |
| `processing_time_ms` | FLOAT | Server processing time |

### `security_alerts`

Anomaly metadata linked to a log record.

| Column | Type | Notes |
|--------|------|-------|
| `alert_id` | UUID (PK) | Auto-generated |
| `log_id` | UUID (FK) | → `system_logs.id`, `ON DELETE CASCADE` |
| `anomaly_score` | FLOAT | 0.0–1.0 decimal scale |
| `model_source` | TEXT | e.g. `brute_force_model` |
| `risk_level` | TEXT | `low` / `medium` / `high` / `critical` |
| `is_resolved` | BOOLEAN | Defaults to `false` |

### `dashboard_metrics` (VIEW)

A single-row aggregated view powering the dashboard KPIs. Computes `total_logs`, `total_alerts`, `anomaly_rate_percentage` (with divide-by-zero protection via `NULLIF`), and `critical_alerts_count`.

---

## Development Roadmap

### ✅ Stage 1 — Synthetic Data Generation

Built the foundational synthetic log generator for smart-city municipal systems.

- Realistic request log generation with device IDs, HTTP methods, endpoints, IP addresses, response codes, payload sizes, and processing times.
- Anomaly injection patterns: brute-force bursts, large-payload exfiltration, and high-latency detection.
- Per-log anomaly scoring with model source attribution and risk-level classification.

```bash
python data_pipeline/generator.py
```

### ✅ Stage 2 — Cloud Ingestion & Relational Threat Triage

Established a resilient, end-to-end cloud data logging architecture with full relational integrity.

- **Dual-Stage Ingestion:** Integrated [`data_pipeline/orchestrator.py`](data_pipeline/orchestrator.py) with [`backend/supabase_client.py`](backend/supabase_client.py) to route streaming synthetic telemetry safely.
- **Relational Threat Triage:** Incoming traffic streams continuously into `system_logs`, while high-risk anomalies (`medium`, `high`, `critical`) are conditionally escalated instantly to `security_alerts` via relational UUID tracking.
- **Resilience Blueprint:** Dynamic `sys.path` mapping eliminates module resolution friction; `KeyboardInterrupt` is handled gracefully to prevent pipeline crash traces during shutdowns.

```bash
python data_pipeline/orchestrator.py
```

### ✅ Stage 3 — Real-Time Dashboard & Threat-Triage UI

Delivered a production-grade React dashboard with live telemetry polling and interactive alert management.

- **Backend API Layer:** FastAPI service exposing overview analytics (via the `dashboard_metrics` view), active alerts, and alert-resolution endpoints with mock-mode fallbacks.
- **Live Dashboard:** React + Vite + Tailwind UI with four KPI cards (total logs, security alerts, anomaly rate, critical incidents) and a real-time active threat feed.
- **Optimized Polling:** A 4-second polling cadence with an in-flight guard ref that prevents overlapping fetches from racing and clobbering state — eliminating the disconnect/reconnect flicker. The `useEffect` cleanup reliably clears the interval on unmount to avoid leakage.
- **Interactive Triage:** One-click optimistic alert resolution with smooth fade-out animations and automatic state reconciliation on the next poll.
- **Resilient UX:** Graceful loading skeletons, error banners, and empty states for every data condition.

```bash
# Terminal 1 — Backend
python backend/api_server.py

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

### ✅ Stage 4 — Spatio-Temporal GNN Data Preparation

Prepared a complete, Colab-ready graph dataset for training a Spatio-Temporal Graph Neural Network (GNN) over the smart-city device mesh. This stage added a high-throughput bulk injector and a graph extractor that together turn 15,000+ raw telemetry rows into PyTorch Geometric–loadable structural arrays.

#### 1. Data Pipeline Enhancements

- **Bulk array-batch injection:** [`data_pipeline/bulk_injector.py`](data_pipeline/bulk_injector.py) replaces row-by-row inserts with native PostgreSQL array batching. Each 1,000-row chunk is sent in a single `.insert()` call (one network round-trip per chunk) via [`bulk_insert_system_logs()`](backend/supabase_client.py:61) and [`bulk_insert_security_alerts()`](backend/supabase_client.py:102), eliminating the remote-database network bottleneck that throttles per-row loops.
- **Scale:** Generates and ingests **15,000+** synthetic `system_logs` plus their matching `security_alerts` in a single run, with pre-generated UUID4 `id`s so every returned database row can be correlated back to its source log regardless of response order.
- **High-risk lateral threat propagation:** A [`simulate_lateral_movement()`](data_pipeline/bulk_injector.py:85) pass walks the declared device topology and, with a 40% probability per critical log, spawns a follow-up high-risk log on a connected device 2–5 seconds later — modeling threat spread across the municipal mesh so the GNN has real spatio-temporal propagation structure to learn from.

```bash
python data_pipeline/bulk_injector.py
```

#### 2. GNN Dataset Extractor

[`data_pipeline/gnn_extractor.py`](data_pipeline/gnn_extractor.py) collapses the live Supabase snapshot into a static spatial graph and serializes it for PyTorch Geometric training:

- **Paging through Supabase:** PostgREST caps each response at 1,000 rows, so [`_fetch_all_rows()`](data_pipeline/gnn_extractor.py:65) slides an inclusive `.range()` window (using the `count="exact"` header, with a short-page fallback) to pull every `system_logs` and `security_alerts` row — only the columns the GNN needs, keeping the wire payload small even at 15k+ rows.
- **Device → integer index mapping:** [`build_device_index_map()`](data_pipeline/gnn_extractor.py:130) assigns every unique device name a stable integer index `0..N-1` (sorted for reproducibility), unioning devices seen in the logs with every device in the declared topology so `edge_index` never references a missing node.
- **Spatial graph topology (COO):** [`build_edge_index()`](data_pipeline/gnn_extractor.py:156) emits one directed edge per declared `(src → tgt)` connection as two parallel index lists — the COO row-pair form that maps 1:1 onto `torch.tensor([sources, targets])` (shape `2 × E`).
- **4-dimensional node features:** [`compute_node_features()`](data_pipeline/gnn_extractor.py:196) builds an `N × 4` matrix per device — `total_logs`, `avg_processing_time_ms`, `avg_payload_size_bytes`, and `total_active_alerts` (unresolved alerts joined to the device via `system_logs.id == security_alerts.log_id`).

```bash
python data_pipeline/gnn_extractor.py
```

#### 3. Artifact Outputs

The extractor writes three Colab-ready files to [`models/dataset/`](models/dataset/):

| File | Format | Contents |
|------|--------|----------|
| [`graph.json`](models/dataset/graph.json) | JSON | Full structural payload — `device_index_map`, COO `edge_index` (`2 × E`), the `N × 4` `node_features` matrix, `feature_names`, and metadata |
| [`node_features.csv`](models/dataset/node_features.csv) | CSV | One row per device (`device_name`, `device_index`, + the 4 feature columns) |
| [`edge_index.csv`](models/dataset/edge_index.csv) | CSV | One row per directed edge (`source_index`, `target_index`) |

These artifacts are ready to be dragged straight into a Google Colab notebook and loaded into a PyTorch Geometric `Data` object for GNN training.

---

## Repository Hygiene

Generated outputs, local virtual environments, environment secrets, and agent pipeline files are excluded from version control via the repository's ignore files (`.gitignore`, `.graphifyignore`). Never commit your `.env` file or Supabase credentials.
