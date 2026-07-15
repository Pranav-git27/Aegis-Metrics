# File Location: data_pipeline/orchestrator.py
"""
data_pipeline/orchestrator.py
Production-grade pipeline that streams synthetic logs to Supabase and triggers security alerts.
"""
import os
import sys
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data_pipeline.generator import generate_log_batch
from backend.supabase_client import insert_system_log, trigger_security_alert

# Configure structured console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def run_pipeline(interval_seconds: int = 2) -> None:
    """
    Continuous ingestion loop that generates synthetic logs,
    stores them in Supabase, and escalates anomalies as security alerts.
    """
    logger.info("Pipeline started – interval %ds", interval_seconds)

    while True:
        try:
            # Fetch a batch of synthetic logs
            logs = generate_log_batch()
            logger.info("Generated batch of %d logs", len(logs))

            for log in logs:
                try:
                    # 1. Aligned Schema Payload: Extract ONLY the columns present in your Supabase table
                    db_payload = {
                        "device_id": log.get("device_id"),
                        "request_method": log.get("request_method"),
                        "endpoint": log.get("endpoint")
                        # 'id' and 'timestamp' are handled automatically by Supabase defaults if omitted
                    }

                    # Stage A – Primary ingestion
                    db_id = insert_system_log(db_payload)
                    
                    if not db_id:
                        logger.error("Skipping alert check: Primary log insertion failed.")
                        continue

                    logger.info("Log inserted successfully with id=%s", db_id)

                    # Stage B – Conditional anomaly escalation (Read from raw 'log' data)
                    risk = log.get("risk_level", "")
                    if risk in ("medium", "high", "critical"):
                        alert_payload = {
                            "log_id": db_id,
                            "anomaly_score": float(log.get("anomaly_score", 0.0)),
                            "risk_level": risk
                        }
                        trigger_security_alert(alert_payload)
                        logger.warning("Anomaly escalated – risk=%s, log_id=%s", risk, db_id)

                except Exception as err:
                    logger.error("Error processing single log: %s", err)

        except Exception as err:
            logger.critical("Pipeline cycle failed: %s", err)

        time.sleep(interval_seconds)

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:
        print("\n" + "="*50)
        logger.info("Pipeline stopped manually by user. Exiting gracefully.")
        print("="*50 + "\n")