# File Location: backend/api_server.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.supabase_client import supabase

logger = logging.getLogger("AegisAPI")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Aegis Metrics API", version="1.0.0")

# CORS: allow the local frontend dev server (and any origin) to communicate.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check() -> Dict[str, str]:
    """Root health-check endpoint."""
    return {"status": "ok", "service": "Aegis Metrics API"}


@app.get("/api/v1/analytics/overview")
def get_analytics_overview() -> Dict[str, Any]:
    """
    Returns aggregated dashboard statistics by querying Supabase directly.

    - total_logs              : count of rows in system_logs
    - total_alerts            : count of rows in gnn_threat_logs
    - anomaly_rate_percentage : (total_alerts / total_logs) * 100, guarded
                                against division by zero
    - quarantined_devices     : count of rows in network_policy_state where
                                status = 'QUARANTINED'
    """
    # Defensive: dev/mock mode when the Supabase client is unavailable.
    if supabase is None:
        logger.warning("Supabase client is None. Returning mock overview payload.")
        return {
            "total_logs": 0,
            "total_alerts": 0,
            "anomaly_rate_percentage": 0.0,
            "quarantined_devices": 0,
        }

    try:
        def _count(table_name: str, apply_filter=None) -> int:
            query = supabase.table(table_name).select("*", count="exact")
            if apply_filter:
                query = apply_filter(query)
            response = query.execute()
            return response.count if response.count is not None else 0

        total_logs = _count("system_logs")
        total_alerts = _count("gnn_threat_logs")
        quarantined_devices = _count(
            "network_policy_state",
            lambda q: q.eq("status", "QUARANTINED"),
        )

        anomaly_rate_percentage = 0.0
        if total_logs > 0:
            anomaly_rate_percentage = round(
                (total_alerts / total_logs) * 100, 2
            )

        return {
            "total_logs": total_logs,
            "total_alerts": total_alerts,
            "anomaly_rate_percentage": anomaly_rate_percentage,
            "quarantined_devices": quarantined_devices,
        }
    except Exception as e:
        logger.error(f"Database error during get_analytics_overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics overview.")


@app.get("/api/v1/alerts/active")
def get_active_alerts() -> List[Dict[str, Any]]:
    """
    Returns all unresolved security alerts (is_resolved = false),
    sorted by anomaly_score descending.
    """
    # Defensive: dev/mock mode when the Supabase client is unavailable.
    if supabase is None:
        logger.warning("Supabase client is None. Returning empty active alerts list.")
        return []

    try:
        response = (
            supabase.table("security_alerts")
            .select("*")
            .eq("is_resolved", False)
            .order("anomaly_score", desc=True)
            .execute()
        )
        return response.data
    except Exception as e:
        logger.error(f"Database error during get_active_alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active alerts.")


@app.put("/api/v1/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str) -> Dict[str, Any]:
    """
    Marks a security alert as resolved (is_resolved = true) for the given
    alert_id. Returns 404 if no matching alert is found.
    """
    # Defensive: dev/mock mode when the Supabase client is unavailable.
    if supabase is None:
        logger.warning(
            f"Supabase client is None. Returning mock resolve response for alert_id: {alert_id}"
        )
        return {
            "message": "Alert resolved successfully (mock)",
            "alert_id": alert_id,
        }

    try:
        response = (
            supabase.table("security_alerts")
            .update({"is_resolved": True})
            .eq("alert_id", alert_id)
            .execute()
        )
        data = response.data
        if not data:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {
            "message": "Alert resolved successfully",
            "alert_id": alert_id,
            "record": data[0],
        }
    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI preserves the correct status code.
        raise
    except Exception as e:
        logger.error(f"Database error during resolve_alert for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
