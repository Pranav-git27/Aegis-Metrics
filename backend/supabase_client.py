# File Location: backend/supabase_client.py
import os
import logging
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None

load_dotenv()
logger = logging.getLogger("SupabaseClient")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: "Client" = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase credentials missing or supabase-py not installed. Running in mock/development mode.")

def insert_system_log(log_data: dict) -> str:
    if supabase:
        try:
            response = supabase.table("system_logs").insert(log_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0].get("id")
        except Exception as e:
            logger.error(f"Database error during insert_system_log: {e}")
            return None
            
    import uuid
    mock_id = str(uuid.uuid4())
    logger.info(f"[MOCK DB] Inserted system log. Generated UUID: {mock_id}")
    return mock_id

def trigger_security_alert(alert_data: dict) -> str:
    """
    Inserts an anomaly incident alert into the security_alerts table.
    """
    if supabase:
        try:
            # Connects directly to your public.security_alerts table seen in the UI
            response = supabase.table("security_alerts").insert(alert_data).execute()
            if response.data and len(response.data) > 0:
                # Returns the newly generated alert_id UUID
                return response.data[0].get("alert_id")
        except Exception as e:
            logger.error(f"Database error during trigger_security_alert: {e}")
            return None  # Keeps the pipeline robust if an insert fails
            
    logger.warning(f"[MOCK DB] Triggered security alert linked to log_id: {alert_data.get('log_id')}")
    return "mock-alert-id"


def bulk_insert_system_logs(logs: list) -> list:
    """
    Bulk-inserts a list of system log dicts in a single .insert() call.

    This performs true bulk array batching (one network round-trip for the
    whole chunk) instead of a row-by-row loop, preventing remote database
    network bottlenecks during large Stage 4 GNN data preparation runs.

    Args:
        logs (list[dict]): List of log payloads, each matching the system_logs
                           schema. Callers should pre-generate a UUID4 `id` per
                           row so returned rows can be correlated back reliably.

    Returns:
        list[str]: The UUIDs of the inserted rows, read from the database
                   response. Returns an empty list on failure. In
                   mock/development mode, echoes back the client-supplied UUIDs
                   so downstream security_alerts can still be wired up.
    """
    if not logs:
        return []

    if supabase:
        try:
            # A single bulk .insert() with the full array of dict payloads.
            response = supabase.table("system_logs").insert(logs).execute()
            if response.data:
                # Read the database-returned UUID for each inserted row.
                return [row.get("id") for row in response.data]
            return []
        except Exception as e:
            logger.error(f"Database error during bulk_insert_system_logs: {e}")
            return []

    # Mock/development mode: echo back the client-supplied UUIDs (or generate
    # mock ones) so the pipeline can still correlate logs with security_alerts.
    mock_ids = [log.get("id") or str(uuid.uuid4()) for log in logs]
    logger.info(f"[MOCK DB] Bulk inserted {len(mock_ids)} system logs.")
    return mock_ids


def bulk_insert_security_alerts(alerts: list) -> list:
    """
    Bulk-inserts a list of security alert dicts in a single .insert() call.

    Args:
        alerts (list[dict]): List of alert payloads, each matching the
                             security_alerts schema (log_id, anomaly_score,
                             model_source, risk_level, is_resolved).

    Returns:
        list[str]: The alert_id UUIDs of the inserted rows, read from the
                   database response. Returns an empty list on failure.
    """
    if not alerts:
        return []

    if supabase:
        try:
            response = supabase.table("security_alerts").insert(alerts).execute()
            if response.data:
                return [row.get("alert_id") for row in response.data]
            return []
        except Exception as e:
            logger.error(f"Database error during bulk_insert_security_alerts: {e}")
            return []

    logger.info(f"[MOCK DB] Bulk inserted {len(alerts)} security alerts.")
    return ["mock-alert-id" for _ in alerts]