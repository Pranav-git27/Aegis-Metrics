-- =============================================================================
-- Migration: dashboard_metrics_view.sql
-- Purpose: Creates a database VIEW named `dashboard_metrics` that aggregates
--          core telemetry statistics for the Aegis Metrics dashboard.
--
-- Aggregated metrics (single-row result set):
--   - total_logs              : Total count of rows in system_logs.
--   - total_alerts            : Total count of rows in security_alerts.
--   - anomaly_rate_percentage : (total_alerts / total_logs) * 100, rounded to
--                               2 decimal places. Uses NULLIF(total_logs, 0)
--                               so the result is NULL (not an error) when no
--                               logs exist, preventing divide-by-zero.
--   - critical_alerts_count   : Count of alerts where risk_level = 'critical'.
--
-- Usage: Apply against the database containing the `system_logs` and
--        `security_alerts` tables (see backend/schema.sql).
-- =============================================================================

CREATE OR REPLACE VIEW dashboard_metrics AS
SELECT
    (SELECT COUNT(*) FROM system_logs) AS total_logs,
    (SELECT COUNT(*) FROM security_alerts) AS total_alerts,
    ROUND(
        ((SELECT COUNT(*) FROM security_alerts)::numeric
            / NULLIF((SELECT COUNT(*) FROM system_logs), 0)) * 100,
        2
    ) AS anomaly_rate_percentage,
    (SELECT COUNT(*) FROM security_alerts WHERE risk_level = 'critical') AS critical_alerts_count;
