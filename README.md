

# 🛡️ Aegis Metrics / Sentinel-Audit

![Python](https://img.shields.io/badge/Python-3.9%2B-0d1117?style=flat-square&logo=python&logoColor=58a6ff)
![PyTorch](https://img.shields.io/badge/PyTorch-GNN-0d1117?style=flat-square&logo=pytorch&logoColor=ee4c2c)
![Supabase](https://img.shields.io/badge/Supabase-Realtime-0d1117?style=flat-square&logo=supabase&logoColor=3ecf8e)
![React](https://img.shields.io/badge/React-Vite-0d1117?style=flat-square&logo=react&logoColor=61dafb)
![Status](https://img.shields.io/badge/Defense-Autonomous-0d1117?style=flat-square)

**Autonomous DevSecOps Threat Detection, Containment & Audit Platform for Smart-City Infrastructure**

Aegis Metrics, also known as **Sentinel-Audit**, is an autonomous DevSecOps platform that converts smart-city telemetry into graph-aware threat decisions and immediate defensive action. It combines PyTorch Geometric GNN inference, Supabase PostgreSQL and Realtime streams, automated device quarantine, immutable mitigation auditing, and a live dark-theme security dashboard.

**Key capabilities:**

- 🔄 High-volume synthetic telemetry generation with lateral-movement simulation
- 🧠 PyTorch GNN inference over the municipal device topology
- 🚨 Persistent device-level assessments in `gnn_threat_logs`
- 🔒 Autonomous quarantine through `network_policy_state`
- 🧾 Automated containment evidence in `gnn_mitigation_actions`
- ⚡ Supabase Realtime streams for threat, policy, and mitigation events
- 🖥️ React threat-operations dashboard with KPI and incident visibility

---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Quick Start](#quick-start)
  - [1. Data Injection](#1-data-injection)
  - [2. GNN Threat Inference](#2-gnn-threat-inference)
  - [3. Autonomous Remediation Agent](#3-autonomous-remediation-agent)
  - [4. Frontend Dashboard](#4-frontend-dashboard)
  - [Optional Backend API](#optional-backend-api)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Development Roadmap](#development-roadmap)
- [Repository Hygiene](#repository-hygiene)

---

## Overview

Aegis Metrics models a smart-city security operations center as a connected device graph. Synthetic telemetry enters Supabase through the bulk injector, is transformed into PyTorch Geometric features, and is evaluated by a trained GNN. Every device assessment is persisted to `gnn_threat_logs`; scores at or above `0.80` activate the remediation agent, which upserts a `QUARANTINED` network policy and records lateral-movement containment in the mitigation audit stream.

Supabase Realtime publishes threat assessments, policy state changes, and mitigation actions to subscribed services and the web dashboard. The existing FastAPI analytics and relational `security_alerts` workflow remain available alongside this autonomous GNN defense loop.

---

## Architecture

```text
┌──────────────────┐   ┌─────────────┐   ┌────────────────────────────┐
│ bulk_injector.py │──▶│ system_logs │──▶│ models/inference_engine.py │
└──────────────────┘   └─────────────┘   └─────────────┬──────────────┘
                                                       │ PyTorch GNN scores
                                                       ▼
                                            ┌─────────────────────┐
                                            │   gnn_threat_logs   │
                                            └──────────┬──────────┘
                                                       │ score >= 0.80
                                                       ▼
                                      ┌───────────────────────────────────┐
                                      │ datapipeline/remediation_agent.py │
                                      └─────────────────┬─────────────────┘
                                                        │ upsert + audit
                              ┌─────────────────────────┴────────────────────────┐
                              ▼                                                  ▼
                 ┌──────────────────────┐                          ┌────────────────────────┐
                 │ network_policy_state │                          │ gnn_mitigation_actions │
                 └───────────┬──────────┘                          └───────────┬────────────┘
                             └─────────────────────┬────────────────────────────┘
                                                   ▼
                                      ┌─────────────────────┐
                                      │  Supabase Realtime  │
                                      └──────────┬──────────┘
                                                 ▼
                                      ┌─────────────────────┐
                                      │    Web Dashboard    │
                                      │ React + Vite + REST │
                                      └─────────────────────┘
```

- **Telemetry layer** — Generates bulk smart-city request events, including connected-device lateral-movement patterns, and stores them in `system_logs`.
- **Inference layer** — Loads graph features and trained PyTorch weights, computes per-device threat probabilities, and inserts assessment batches into `gnn_threat_logs`.
- **Remediation layer** — Polls high-risk assessments, quarantines affected devices through conflict-safe policy upserts, emits containment logs, and writes audit records.
- **Streaming and presentation layer** — Supabase Realtime publishes database changes for live dashboard consumption; FastAPI continues to provide aggregate REST analytics and alert controls.

---

## Project Structure

```text
Aegis Metrics/
├── backend/
│   ├── api_server.py                         # FastAPI application and REST endpoints
│   ├── supabase_client.py                    # Shared Supabase ingestion helpers
│   ├── schema.sql                            # Core telemetry and alert DDL
│   ├── database/
│   │   └── gnn_remediation_schema.sql        # GNN, policy, audit, and Realtime DDL
│   └── migrations/
│       └── dashboard_metrics_view.sql        # Aggregated metrics view
├── data_pipeline/
│   ├── generator.py                          # Synthetic telemetry generator
│   ├── orchestrator.py                       # Continuous legacy ingestion loop
│   ├── bulk_injector.py                      # Bulk telemetry and lateral movement
│   └── gnn_extractor.py                      # Graph topology and feature extraction
├── datapipeline/
│   └── remediation_agent.py                  # Autonomous quarantine and audit worker
├── models/
│   ├── inference_engine.py                   # PyTorch GNN inference and threat persistence
│   ├── gnn_threat_model.pt                   # Trained model weights (local artifact)
│   └── dataset/
│       ├── graph.json                        # Full graph payload
│       ├── node_features.csv                 # Per-device GNN feature matrix
│       └── edge_index.csv                    # Directed COO edge list
├── frontend/
│   ├── package.json
│   └── src/                                  # React dashboard and API client
├── requirements.txt
└── README.md
```

> The canonical schema reference is [`backend/database/gnn_remediation_schema.sql`](backend/database/gnn_remediation_schema.sql). If upgrading an older checkout where it exists directly under `backend/`, relocate it into `backend/database/` before applying the documented setup.

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

```dotenv
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
# Optional compatibility fallback used by the inference engine and legacy modules:
SUPABASE_KEY=your-supabase-key
```

> Use `SUPABASE_SERVICE_ROLE_KEY` for the autonomous inference and remediation workers because they perform privileged inserts and policy updates. Keep `.env` local, never expose a service-role key to the browser, and never commit it to source control.

---

## Database Setup

Apply the core schema in [`backend/schema.sql`](backend/schema.sql), the dashboard view in [`backend/migrations/dashboard_metrics_view.sql`](backend/migrations/dashboard_metrics_view.sql), and the autonomous-defense schema in [`backend/database/gnn_remediation_schema.sql`](backend/database/gnn_remediation_schema.sql) through the Supabase SQL Editor. The remediation schema contains the following DDL:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.gnn_threat_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT NOT NULL,
    threat_score DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'CRITICAL',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.network_policy_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'NORMAL',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.gnn_mitigation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    threat_score DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'EXECUTED',
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.gnn_threat_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.network_policy_state DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.gnn_mitigation_actions DISABLE ROW LEVEL SECURITY;

ALTER PUBLICATION supabase_realtime ADD TABLE public.gnn_threat_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.network_policy_state;
ALTER PUBLICATION supabase_realtime ADD TABLE public.gnn_mitigation_actions;
```

> `network_policy_state.device_name` is unique because the remediation agent uses it as the `ON CONFLICT` target when atomically creating or updating quarantine state. Publication commands should only be applied once per table; Supabase reports an error if a table is already a member of `supabase_realtime`.

---

## Quick Start

Install the Python dependencies from [`requirements.txt`](requirements.txt), configure the Supabase environment variables, apply the database schemas, and then run the autonomous pipeline in this order.

### 1. Data Injection

Generate bulk telemetry and lateral-movement samples, then insert them into `system_logs`:

```bash
python datapipeline/bulk_injector.py
```

### 2. GNN Threat Inference

Load the graph dataset and trained model, compute device threat scores, and persist assessments to `gnn_threat_logs`:

```bash
python models/inference_engine.py
```

### 3. Autonomous Remediation Agent

Start the continuous worker that detects scores at or above `0.80`, quarantines devices, and writes mitigation audits:

```bash
python datapipeline/remediation_agent.py
```

The worker shuts down cleanly on `Ctrl+C`. To process the currently qualifying threat rows once and exit, add the `--once` option.

### 4. Frontend Dashboard

From [`frontend/`](frontend/), launch the Vite development server:

```bash
npm run dev
```

The dashboard is served on `http://localhost:5173` by default. Install packages with `npm install` first when setting up a fresh checkout.

### Optional Backend API

Run the FastAPI analytics and alert-management service from the project root:

```bash
python backend/api_server.py
```

The API is available at `http://localhost:8000`, with interactive Swagger documentation at `http://localhost:8000/docs`. The frontend API base URL is configured in [`frontend/src/api.js`](frontend/src/api.js).

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

### ✅ Stage 5 — GNN Threat Inference Engine

Operationalized the trained graph model as a local inference service in [`models/inference_engine.py`](models/inference_engine.py).

- Loads the PyTorch Geometric graph tensors and trained `ThreatGNN` weights.
- Computes a class-1 threat probability for every device node.
- Maps each prediction to `CRITICAL` at `threat_score >= 0.80`, otherwise `HEALTHY`.
- Bulk-inserts device assessments into `gnn_threat_logs` using Supabase service credentials loaded through `python-dotenv`.
- Logs the number of successfully persisted assessments and handles Supabase API failures without suppressing the local report.

```bash
python models/inference_engine.py
```

### ✅ Stage 6 — Autonomous Remediation Agent

Closed the detection-to-response loop with [`datapipeline/remediation_agent.py`](datapipeline/remediation_agent.py), delivering autonomous policy quarantine and audit streams.

- Polls `gnn_threat_logs` for assessments at or above the `0.80` defense threshold.
- Upserts `{device_name, status: "QUARANTINED"}` into `network_policy_state` with `device_name` as the conflict key.
- Emits structured security logs documenting lateral-movement containment.
- Inserts traceable mitigation evidence into `gnn_mitigation_actions` with the device, action, and triggering score.
- Publishes threat, quarantine, and mitigation state through Supabase Realtime for dashboard subscribers.
- Handles malformed records, transient API failures, and operator shutdown without terminating on an unhandled traceback.

```bash
python datapipeline/remediation_agent.py
```

---

## Repository Hygiene

Generated outputs, local virtual environments, environment secrets, and agent pipeline files are excluded from version control via the repository's ignore files (`.gitignore`, `.graphifyignore`). Never commit your `.env` file or Supabase credentials.
