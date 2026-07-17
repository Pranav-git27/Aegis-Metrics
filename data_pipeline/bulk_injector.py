# File Location: data_pipeline/bulk_injector.py
"""
Bulk data injector for Stage 4 (Spatio-Temporal GNN Data Preparation).
Generates 15,000 synthetic system_logs and corresponding security_alerts with lateral movement sequences.
"""
import os
import sys
import time
import logging
import random
import uuid
from datetime import datetime, timedelta
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.supabase_client import bulk_insert_system_logs, bulk_insert_security_alerts

# --- Configuration ---
DEVICE_CONNECTIONS = {
    "TRAFFIC_LIGHT_NODE_04": ["TRAFFIC_LIGHT_NODE_01", "NETWORK_HUB_A", "PUMP_CONTROL_03"],
    "WATER_PUMP_CENTRAL": ["PUMP_CONTROL_03", "TRAFFIC_LIGHT_NODE_04", "NETWORK_HUB_A"],
    "STREET_LIGHT_HUB_12": ["NETWORK_HUB_A", "NETWORK_HUB_B", "PUMP_CONTROL_01"],
    "TRAFFIC_LIGHT_NODE_01": ["TRAFFIC_LIGHT_NODE_04", "PUMP_CONTROL_01", "NETWORK_HUB_B"],
    "NETWORK_HUB_A": ["TRAFFIC_LIGHT_NODE_04", "WATER_PUMP_CENTRAL", "STREET_LIGHT_HUB_12"],
    "NETWORK_HUB_B": ["STREET_LIGHT_HUB_12", "TRAFFIC_LIGHT_NODE_01", "NETWORK_HUB_A"],
    "PUMP_CONTROL_03": ["WATER_PUMP_CENTRAL", "TRAFFIC_LIGHT_NODE_01", "PUMP_CONTROL_02"],
    "PUMP_CONTROL_01": ["NETWORK_HUB_B", "PUMP_CONTROL_02", "STREET_LIGHT_HUB_12"],
    "PUMP_CONTROL_02": ["PUMP_CONTROL_03", "PUMP_CONTROL_01", "NETWORK_HUB_A"]
}

# Configure structured console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def generate_single_log(device_id, log_type="normal"):
    """
    Generate a single log entry for the given device ID.

    Args:
        device_id (str): ID of the device generating the log
        log_type (str): "normal", "anomaly", or "high_risk"

    Returns:
        dict: Log entry matching Supabase schema
    """
    from datetime import datetime, timedelta

    # Base log structure
    log = {
        "id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": (datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))).isoformat(),
        "request_method": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "endpoint": random.choice(["/api/v1/telemetry", "/api/v1/control", "/auth/login"]),
        "ip_address": ".".join(str(random.randint(0, 255)) for _ in range(4)),
        "response_code": random.choice([200] + [404, 500] * 2),
        "payload_size_bytes": random.randint(100, 5000),
        "processing_time_ms": round(random.uniform(5.0, 150.0), 1),
        "anomaly_score": 0.0,
        "risk_level": "low",
        "is_resolved": False,
        "model_source": "baseline_model"
    }

    if log_type == "anomaly":
        log["anomaly_score"] = round(random.uniform(0.6, 0.9), 2)
        log["model_source"] = random.choice(["brute_force_model", "exfiltration_model"])
        log["risk_level"] = random.choice(["medium", "high"])
        log["is_resolved"] = False

    elif log_type == "high_risk":
        log["anomaly_score"] = round(random.uniform(0.8, 0.95), 2)
        log["model_source"] = random.choice(["brute_force_model", "exfiltration_model"])
        log["risk_level"] = "critical"
        log["is_resolved"] = False

    return log

def simulate_lateral_movement(all_logs):
    """
    Simulate lateral movement sequences where anomalies propagate between connected devices.

    Args:
        all_logs (list): List of log entries to modify for lateral movement

    Returns:
        list: Modified logs with lateral movement sequences added
    """
    logger.info("Simulating lateral movement sequences...")

    # Create a mapping of device_id to list of logs for that device
    device_logs = {}
    for log in all_logs:
        if log["device_id"] not in device_logs:
            device_logs[log["device_id"]] = []
        device_logs[log["device_id"]].append(log)

    # Process each device for lateral movement
    lateral_sequences_added = 0
    processed_devices = set()

    for device_id, device_log_list in device_logs.items():
        # Only process high-risk or anomaly logs as starting points
        high_risk_logs = [log for log in device_log_list if log["risk_level"] in ("high", "critical")]

        if not high_risk_logs:
            continue

        for high_risk_log in high_risk_logs:
            # Only create lateral movement from high-risk logs (not all anomalies)
            if high_risk_log["risk_level"] == "critical":
                # Simulate connected device compromise with 40% probability
                connected_devices = DEVICE_CONNECTIONS.get(device_id, [])
                if connected_devices and random.random() < 0.4:
                    target_device = random.choice(connected_devices)
                    time_offset_seconds = random.randint(2, 5)  # 2-5 seconds later

                    # Generate a lateral movement log for the target device
                    # This represents the threat spreading to the connected device
                    lateral_log = generate_single_log(target_device, log_type="high_risk")

                    # Set timestamp to happen after the original log's timestamp
                    original_time = datetime.fromisoformat(high_risk_log["timestamp"])
                    lateral_time = original_time + timedelta(seconds=time_offset_seconds)
                    lateral_log["timestamp"] = lateral_time.isoformat()

                    # Mark this as a lateral movement event
                    lateral_log["lateral_movement_trigger"] = True
                    lateral_log["original_device_id"] = device_id

                    # Find the log list for target device and add this lateral log
                    if target_device in device_logs:
                        # Add lateral log to target device's logs
                        device_logs[target_device].append(lateral_log)
                        all_logs.append(lateral_log)
                        lateral_sequences_added += 1

                        logger.debug(f"Created lateral movement: {device_id} -> {target_device} after {time_offset_seconds}s")

    logger.info(f"Added {lateral_sequences_added} lateral movement sequences")
    return all_logs

def generate_and_insert_data():
    """
    Generate 15,000 synthetic logs and corresponding security alerts with lateral movement.
    """
    logger.info("Starting bulk data injection for Stage 4 (Spatio-Temporal GNN Data Preparation)")

    # Target number of logs including lateral movement
    TARGET_LOG_COUNT = 15000
    actual_inserted = 0
    alerts_triggered = 0

    logger.info(f"Generating {TARGET_LOG_COUNT} synthetic logs...")

    # Phase 1: Generate all logs (including lateral movement)
    all_logs = []
    logs_generated = 0

    while logs_generated < TARGET_LOG_COUNT:
        # Generate a batch of logs
        current_batch_size = min(1000, TARGET_LOG_COUNT - logs_generated)  # Larger batches for efficiency

        for _ in range(current_batch_size):
            # Determine log type based on probability
            p = random.random()
            if p < 0.05:  # 5% high-risk
                log = generate_single_log(random.choice(list(DEVICE_CONNECTIONS.keys())), log_type="high_risk")
            elif p < 0.15:  # 10% normal anomaly (additional 10%)
                log = generate_single_log(random.choice(list(DEVICE_CONNECTIONS.keys())), log_type="anomaly")
            else:  # 85% normal
                log = generate_single_log(random.choice(list(DEVICE_CONNECTIONS.keys())), log_type="normal")

            all_logs.append(log)

        logs_generated += current_batch_size
        if logs_generated % 2000 == 0:
            logger.info(f"Generated {logs_generated}/{TARGET_LOG_COUNT} logs...")

    logger.info(f"Total logs generated: {len(all_logs)}")

    # Phase 2: Simulate lateral movement sequences
    all_logs = simulate_lateral_movement(all_logs)

    # Phase 3: Insert logs into Supabase using true bulk array batching.
    # Instead of a row-by-row for loop (one network round-trip per log, which
    # bottlenecks on the remote database), we build a list of dict payloads and
    # run a single bulk .insert() per 1000-row chunk, then read the returned
    # database UUIDs to build the matching security_alerts batch.
    logger.info("Inserting logs into Supabase via bulk array batching...")

    batch_size = 1000
    total_batches = math.ceil(len(all_logs) / batch_size)

    for i in range(0, len(all_logs), batch_size):
        batch = all_logs[i:i + batch_size]
        batch_number = (i // batch_size) + 1
        logger.info(f"Processing batch {batch_number} of {total_batches} ({len(batch)} rows)")

        try:
            # Build the array of dict payloads for this chunk, including ALL
            # rich GNN metric features (ip_address, response_code,
            # payload_size_bytes, processing_time_ms) plus the spatio-temporal
            # timestamp. A pre-generated UUID4 `id` is sent so each returned
            # row can be reliably correlated back to its source log regardless
            # of the response row order.
            log_payloads = [
                {
                    "id": log.get("id"),
                    "timestamp": log.get("timestamp"),
                    "device_id": log.get("device_id"),
                    "request_method": log.get("request_method"),
                    "endpoint": log.get("endpoint"),
                    "ip_address": log.get("ip_address"),
                    "response_code": log.get("response_code"),
                    "payload_size_bytes": log.get("payload_size_bytes"),
                    "processing_time_ms": log.get("processing_time_ms"),
                }
                for log in batch
            ]

            # Single bulk .insert() for the entire 1000-row chunk.
            inserted_ids = bulk_insert_system_logs(log_payloads)
            actual_inserted += len(inserted_ids)

            if not inserted_ids:
                logger.warning(f"Batch {batch_number}: no logs inserted; skipping alert generation.")
                continue

            # Read the returned database UUIDs to construct the matching batch
            # array for security_alerts. Only logs that were actually inserted
            # (and carry a medium/high/critical risk level) generate an alert.
            inserted_id_set = set(inserted_ids)
            alert_payloads = []
            for log in batch:
                if log.get("risk_level") not in ("medium", "high", "critical"):
                    continue
                # Correlate via the UUID returned by the database.
                log_id = log.get("id")
                if log_id not in inserted_id_set:
                    continue
                alert_payloads.append({
                    "log_id": log_id,
                    "anomaly_score": float(log.get("anomaly_score", 0.0)),
                    "model_source": log.get("model_source"),
                    "risk_level": log.get("risk_level"),
                    "is_resolved": bool(log.get("is_resolved", False)),
                })

            # Single bulk .insert() for the matching security_alerts chunk.
            if alert_payloads:
                inserted_alert_ids = bulk_insert_security_alerts(alert_payloads)
                alerts_triggered += len(inserted_alert_ids)

        except Exception as e:
            logger.error(f"Error processing batch {batch_number}: {e}")
            continue

    logger.info("=" * 60)
    logger.info(f"BULK INJECTION COMPLETE")
    logger.info(f"Total logs generated: {len(all_logs)}")
    logger.info(f"Logs inserted: {actual_inserted}")
    logger.info(f"Security alerts triggered: {alerts_triggered}")
    logger.info(f"Lateral movement sequences added: {sum(1 for log in all_logs if log.get('lateral_movement_trigger', False))}")
    logger.info("=" * 60)

    return {
        "total_logs_generated": len(all_logs),
        "logs_inserted": actual_inserted,
        "alerts_triggered": alerts_triggered,
        "lateral_sequences": sum(1 for log in all_logs if log.get('lateral_movement_trigger', False))
    }

if __name__ == "__main__":
    try:
        result = generate_and_insert_data()
        logger.info("Data injection completed successfully!")
    except Exception as e:
        logger.error(f"Data injection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)