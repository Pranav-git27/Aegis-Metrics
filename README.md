# Aegis-Metrics — Autonomous GNN-Driven DevSecOps Engine

![Python](https://img.shields.io/badge/Python-3.9%2B-0d1117?style=flat-square&logo=python&logoColor=58a6ff)
![PyTorch](https://img.shields.io/badge/PyTorch-GNN-0d1117?style=flat-square&logo=pytorch&logoColor=ee4c2c)
![Supabase](https://img.shields.io/badge/Supabase-Realtime-0d1117?style=flat-square&logo=supabase&logoColor=3ecf8e)
![React](https://img.shields.io/badge/React-Vite-0d1117?style=flat-square&logo=react&logoColor=61dafb)
![Status](https://img.shields.io/badge/Defense-Autonomous-0d1117?style=flat-square)

**Live telemetry in. Graph-aware containment out.**

Aegis-Metrics is an autonomous DevSecOps threat-detection and response platform for connected infrastructure. It ingests live network telemetry into Supabase Postgres, detects spatial-temporal anomalies with a PyTorch Graph Neural Network (GNN), automatically quarantines compromised nodes, records every mitigation action, and streams real-time threat telemetry over Supabase WebSockets to a dark-mode React SOC dashboard.

## Table of Contents

- [System Architecture](#system-architecture)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Repository Structure](#repository-structure)
- [Data Flow](#data-flow)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Installation](#installation)
- [Running Aegis-Metrics](#running-aegis-metrics)
- [Automated Integration Tests](#automated-integration-tests)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Operational Notes](#operational-notes)
- [Development Roadmap](#development-roadmap)

## System Architecture

```text
+-----------------------+     +---------------------+     +------------------------------+
| Telemetry Ingestion   | --> | Supabase Postgres   | --> | PyTorch GNN Inference Engine |
| generator / injector  |     | logs + graph state  |     | spatial-temporal scoring     |
+-----------------------+     +---------------------+     +---------------+--------------+
                                                                            |
                                                                            v
+-----------------------+     +---------------------+     +------------------------------+
| React SOC Dashboard   | <-- | Supabase Realtime   | <-- | Remediation Agent            |
| dark-mode operations  |     | WebSocket events    |     | quarantine + mitigation log  |
+-----------------------+     +---------------------+     +------------------------------+
```

Canonical workflow:

```text
[Telemetry Ingestion]
          -> [Supabase Postgres]
          -> [PyTorch GNN Inference Engine]
          -> [Remediation Agent]
          -> [React SOC Dashboard]
```

The ingestion layer stores municipal network packets in `system_logs`. The graph extractor aggregates device telemetry and active alerts into node features, while the inference engine evaluates the generated graph and persists device-level scores in `gnn_threat_logs`. Threats at or above the remediation threshold are isolated in `network_policy_state` and documented in `gnn_mitigation_actions`. Supabase Realtime publishes these changes to the dashboard through `postgres_changes` subscriptions.

## Key Features

### Graph Neural Network Engine

- PyTorch and PyTorch Geometric architecture combining graph convolution and graph attention layers.
- Spatial graph topology models relationships between connected smart-city devices.
- Node features combine telemetry volume, average latency, average payload size, and unresolved alert count.
- Device-level threat probabilities are persisted to `gnn_threat_logs` and classified as `CRITICAL` or `HEALTHY`.

### Autonomous Remediation Agent

- Detects threat records at or above the configured response threshold.
- Atomically upserts compromised devices into `network_policy_state` with `status = 'QUARANTINED'`.
- Emits structured containment logs for security operations and incident response.
- Writes traceable action records to `gnn_mitigation_actions` for auditing and compliance.

### Realtime Supabase Replication

- Uses Supabase Realtime WebSockets and `postgres_changes` subscriptions.
- Streams inserts, updates, and deletes from threat, mitigation, and network-policy tables.
- Designed for low-latency, sub-100ms pushes under healthy network and Supabase project conditions.
- Removes channels during React component cleanup to prevent duplicate subscriptions and resource leaks.

### React + Tailwind SOC Console

- Dark-mode operations interface built with React, Vite, Tailwind CSS, and Lucide icons.
- Live threat and autonomous mitigation tables.
- Dynamic counters for telemetry volume, active detections, anomaly rate, and quarantined devices.
- Realtime network-policy grid with quarantine state and update timestamps.
- Loading, empty, and degraded-connection states for operational resilience.

### Automated Integration Test Suite

- Pytest suite exercises ingestion, GNN inference, remediation, and mitigation auditing end to end.
- Uses the live Supabase configuration loaded from `.env`.
- Verifies a synthetic `TEST_PUMP_99` packet is classified `CRITICAL` with a score above `0.85`.
- Includes a teardown fixture that removes test rows and restores generated graph artifacts.
- Prints clear pass-stage messages while retaining standard pytest failure diagnostics.

## Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Telemetry | Python | Synthetic packet generation and high-volume ingestion |
| Data store | Supabase Postgres | Telemetry, threat, policy, and audit persistence |
| Realtime | Supabase Realtime | WebSocket `postgres_changes` replication |
| Graph ML | PyTorch, PyTorch Geometric | GCN/GAT threat classification |
| API | FastAPI, Uvicorn | Dashboard analytics and alert APIs |
| Frontend | React, Vite, Tailwind CSS | Dark-mode SOC dashboard |
| Testing | pytest | Live end-to-end pipeline verification |

## Repository Structure

```text
Aegis Metrics/
|-- backend/
|   |-- api_server.py                    # FastAPI analytics service
|   |-- schema.sql                       # Core telemetry and alert schema
|   |-- gnn_remediation_schema.sql       # Threat, policy, audit, and Realtime schema
|   |-- supabase_client.py               # Shared Supabase ingestion helpers
|   `-- migrations/
|       `-- dashboard_metrics_view.sql   # Dashboard KPI view
|-- data_pipeline/
|   |-- generator.py                     # Synthetic telemetry generator
|   |-- bulk_injector.py                 # Batched ingestion and lateral movement
|   |-- gnn_extractor.py                 # Supabase-to-graph feature extraction
|   `-- orchestrator.py                  # Continuous legacy ingestion loop
|-- datapipeline/
|   `-- remediation_agent.py             # Autonomous quarantine and audit worker
|-- models/
|   |-- inference_engine.py              # GNN inference and threat persistence
|   |-- gnn_threat_model.pt              # Trained model weights
|   `-- dataset/                         # Generated graph artifacts
|-- frontend/
|   |-- package.json
|   `-- src/                             # React SOC console
|-- tests/
|   `-- test_pipeline.py                 # End-to-end integration suite
|-- requirements.txt
`-- README.md
```

## Data Flow

1. `data_pipeline/bulk_injector.py` generates realistic traffic, including high-risk lateral-movement patterns, and bulk-inserts packets into `system_logs`.
2. `data_pipeline/gnn_extractor.py` reads telemetry and unresolved alerts, builds a stable device index, creates graph edges, and writes node features to `models/dataset/`.
3. `models/inference_engine.py` loads the graph and trained weights, calculates class-1 threat probabilities, and inserts assessments into `gnn_threat_logs`.
4. `datapipeline/remediation_agent.py` processes qualifying threats, quarantines devices, and writes mitigation evidence.
5. Supabase Realtime broadcasts table changes to the React dashboard, while FastAPI serves aggregate KPI data.

## Prerequisites

- Python 3.9 or newer
- Node.js 18 or newer
- npm 9 or newer
- A Supabase project
- A Supabase service-role key for privileged pipeline and integration-test operations
- Applied database schemas and enabled Realtime publication for the three autonomous-defense tables

## Environment Configuration

Create a `.env` file in the repository root:

```dotenv
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Compatibility fallback used by legacy modules when no service-role key is set.
SUPABASE_KEY=your-supabase-key
```

The integration suite and inference engine prefer `SUPABASE_SERVICE_ROLE_KEY`, then fall back to `SUPABASE_KEY`. The remediation agent requires the service-role key because it performs privileged policy updates and audit inserts.

Create `frontend/.env` for the browser client:

```dotenv
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-public-anon-key

```

Never expose `SUPABASE_SERVICE_ROLE_KEY` in a `VITE_*` variable or commit either environment file. Vite embeds `VITE_*` values into the browser bundle, so only the public Supabase anon key belongs in `frontend/.env`.

## Database Setup

Apply these SQL files through the Supabase SQL Editor in order:

1. `backend/schema.sql`
2. `backend/gnn_remediation_schema.sql`
3. `backend/migrations/dashboard_metrics_view.sql`

The autonomous schema creates:

- `gnn_threat_logs` for GNN assessments.
- `network_policy_state` for current device isolation state.
- `gnn_mitigation_actions` for remediation audit evidence.
- Supabase Realtime publication entries for all three tables.

`network_policy_state.device_name` must remain unique because the remediation agent uses it as the `ON CONFLICT` target. If a table is already included in the `supabase_realtime` publication, omit or skip its duplicate publication statement.

## Installation

From the repository root, create and activate a virtual environment, then install backend and test dependencies.

### Windows Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest
```

Install frontend dependencies:

```cmd
cd frontend
npm install
```

## Running Aegis-Metrics

Run each service from a separate terminal. Python commands assume the current directory is the repository root.

### 1. Start the FastAPI Backend

```cmd
python backend/api_server.py
```

The API is available at `http://localhost:8000`, with interactive OpenAPI documentation at `http://localhost:8000/docs`.

### 2. Start the Frontend Development Server

```cmd
cd frontend
npm run dev
```

Vite serves the SOC dashboard at `http://localhost:5173` by default.

### 3. Inject Telemetry

Generate and bulk-insert synthetic telemetry and lateral-movement events:

```cmd
python data_pipeline/bulk_injector.py
```

### 4. Build the Live Graph Dataset

Refresh graph topology and node features from Supabase before inference:

```cmd
python data_pipeline/gnn_extractor.py
```

### 5. Run GNN Inference

Load the trained model, score every graph node, and persist threat assessments:

```cmd
python models/inference_engine.py
```

### 6. Run Autonomous Remediation

Start continuous threat polling and remediation:

```cmd
python datapipeline/remediation_agent.py
```

To process currently qualifying threat rows once and exit:

```cmd
python datapipeline/remediation_agent.py --once
```

### Recommended Pipeline Order

```text
bulk_injector.py
    -> gnn_extractor.py
    -> inference_engine.py
    -> remediation_agent.py
    -> React SOC dashboard
```

## Automated Integration Tests

The integration test uses the configured live Supabase project and creates a synthetic device named `TEST_PUMP_99`. It validates all four pipeline stages and removes synthetic records from `system_logs`, `gnn_threat_logs`, `network_policy_state`, and `gnn_mitigation_actions` during teardown. The linked `security_alerts` row is removed through the schema's `ON DELETE CASCADE` relationship.

Run the suite serially from the repository root:

```cmd
pytest tests/test_pipeline.py -v -s
```

Alternatively, invoke pytest through the active Python interpreter:

```cmd
python -m pytest tests/test_pipeline.py -v -s
```

Expected stages:

1. `test_anomaly_ingestion` inserts and verifies high-risk telemetry.
2. `test_gnn_threat_detection` rebuilds graph features, runs the real model, and verifies a `CRITICAL` threat score above `0.85`.
3. `test_autonomous_remediation` executes the remediation agent and verifies `QUARANTINED` policy state.
4. `test_mitigation_audit_log` verifies an `EXECUTED` mitigation audit record.

Because this is a live integration suite, do not run it against a Supabase project containing a legitimate device named `TEST_PUMP_99`. The module fixture removes rows matching that reserved test identifier before and after execution.

## API Reference

All operational endpoints are served by `backend/api_server.py`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service health check |
| `GET` | `/api/v1/analytics/overview` | Telemetry, threat, anomaly, and quarantine KPIs |
| `GET` | `/api/v1/alerts/active` | Unresolved relational security alerts sorted by anomaly score |
| `PUT` | `/api/v1/alerts/{alert_id}/resolve` | Resolve an alert in the legacy triage workflow |

Example overview response:

```json
{
  "total_logs": 12480,
  "total_alerts": 612,
  "anomaly_rate_percentage": 4.91,
  "quarantined_devices": 18
}
```

## Data Model

### `system_logs`

Raw network and request telemetry, including device ID, endpoint, source IP, response code, payload size, and processing time.

### `security_alerts`

Relational anomaly metadata linked to `system_logs.id`. Unresolved records contribute to the GNN node feature vector.

### `gnn_threat_logs`

| Column | Purpose |
|---|---|
| `device_name` | Graph node or managed device identifier |
| `threat_score` | Predicted class-1 compromise probability |
| `status` | `CRITICAL` or `HEALTHY` assessment |
| `detected_at` | Threat persistence timestamp |

### `network_policy_state`

| Column | Purpose |
|---|---|
| `device_name` | Unique managed device identifier |
| `status` | Current `NORMAL` or `QUARANTINED` state |
| `updated_at` | Last policy-state update |

### `gnn_mitigation_actions`

| Column | Purpose |
|---|---|
| `device_name` | Remediated device identifier |
| `action_taken` | Human-readable containment action |
| `threat_score` | Score that triggered remediation |
| `status` | Action state, normally `EXECUTED` |
| `executed_at` | Audit timestamp |

## Operational Notes

- The default model classification threshold is `0.80`; the integration test intentionally enforces the stricter requirement `> 0.85`.
- Run graph extraction before inference whenever live telemetry or device topology changes.
- The remediation agent currently processes qualifying records from `gnn_threat_logs`; use one-shot mode for controlled jobs or continuous mode for active defense.
- Supabase Realtime latency depends on project region, network conditions, database load, and client location. Sub-100ms delivery is a target, not a hard service guarantee.
- Use a service-role key only in trusted backend processes. Configure Row Level Security policies before exposing production tables to browser clients.
- The integration test temporarily rewrites generated files in `models/dataset/` and restores their original bytes during teardown.

## Development Roadmap

### Completed

- **Stage 1 — Synthetic Telemetry:** realistic smart-city request generation and anomaly injection.
- **Stage 2 — Cloud Ingestion:** resilient Supabase persistence and relational security triage.
- **Stage 3 — SOC Dashboard:** FastAPI analytics with a React/Vite/Tailwind operations console.
- **Stage 4 — Graph Preparation:** paginated extraction, deterministic node mapping, COO topology, and four-dimensional node features.
- **Stage 5 — GNN Inference:** trained PyTorch Geometric model loading, probability scoring, and Supabase threat persistence.
- **Stage 6 — Autonomous Remediation:** device quarantine, structured containment logging, and mitigation auditing.
- **Stage 7 — Integration Validation:** live pytest coverage across ingestion, inference, remediation, audit verification, and cleanup.

### Production Hardening

- Add durable threat-processing state or queue semantics to prevent repeated remediation across agent restarts.
- Add model/version metadata and feature-schema validation to every persisted inference.
- Add CI unit tests with mocked Supabase clients alongside opt-in live integration tests.
- Add authentication, production Row Level Security policies, and centralized secret management.
- Add deployment manifests, health probes, structured observability, and alerting for each pipeline stage.

## Repository Hygiene

Generated outputs, virtual environments, local secrets, and agent state should remain excluded through `.gitignore` and `.graphifyignore`. Never commit `.env`, `frontend/.env`, service-role credentials, model training secrets, or production database exports.
