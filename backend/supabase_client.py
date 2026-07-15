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