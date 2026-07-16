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
    Returns aggregated dashboard statistics by querying the
    `dashboard_metrics` database view.
    """
    # Defensive: dev/mock mode when the Supabase client is unavailable.
    if supabase is None:
        logger.warning("Supabase client is None. Returning mock overview payload.")
        return {
            "total_logs": 0,
            "total_alerts": 0,
            "anomaly_rate_percentage": None,
            "critical_alerts_count": 0,
        }

    try:
        response = supabase.table("dashboard_metrics").select("*").execute()
        data = response.data
        if data and len(data) > 0:
            return data[0]
        # View returned no rows: return a sensible zeroed default.
        logger.info("dashboard_metrics view returned no rows. Returning default zeros.")
        return {
            "total_logs": 0,
            "total_alerts": 0,
            "anomaly_rate_percentage": None,
            "critical_alerts_count": 0,
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
