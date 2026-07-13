# Aegis Metrics

Aegis Metrics is a smart-city security monitoring project for generating and structuring municipal system request logs. The repository includes a synthetic data pipeline, a database schema, and frontend/backend project directories for building an anomaly-monitoring workflow.

## Project Structure

- `data_pipeline/` - Python utilities for generating realistic smart-city server request logs.
- `backend/` - Database schema resources for system logs and security alerts.
- `frontend/` - Frontend application directory.
- `models/` - Model-related project assets.
- `requirements.txt` - Python dependencies used by the data pipeline and supporting services.

## Data Pipeline

The synthetic log generator creates batches of municipal system request logs with fields aligned to the database schema, including device IDs, request methods, endpoints, IP addresses, response codes, payload sizes, processing times, anomaly scores, model sources, risk levels, and resolution status.

Example usage:

```bash
python data_pipeline/generator.py
```

## Database Schema

The schema defines:

- `system_logs` for raw request telemetry.
- `security_alerts` for anomaly metadata linked to log records.

## Dependencies

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

Core dependency areas include data generation and manipulation, backend APIs, machine learning, and database operations.

## Repository Hygiene

Generated outputs, local virtual environments, environment secrets, and agent pipeline files are excluded from version control through the repository ignore files.
