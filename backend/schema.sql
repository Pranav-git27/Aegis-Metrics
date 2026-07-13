CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT now(),
    device_id TEXT,
    request_method TEXT,
    endpoint TEXT,
    ip_address TEXT,
    response_code INTEGER,
    payload_size_bytes INTEGER,
    processing_time_ms FLOAT
);

CREATE TABLE security_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES system_logs(id) ON DELETE CASCADE,
    anomaly_score FLOAT,
    model_source TEXT,
    risk_level TEXT,
    is_resolved BOOLEAN DEFAULT false
);
