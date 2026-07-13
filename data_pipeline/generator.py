"""
data_pipeline/generator.py
Generates realistic Smart City server request logs matching the Supabase schema.
"""

import random
import uuid
import ipaddress
from datetime import datetime, timedelta
import json  # Required if you later save logs to files

# --- Configuration ---
MUNICIPAL_SYSTEMS = [
    "TRAFFIC_LIGHT_NODE_04",
    "WATER_PUMP_CENTRAL",
    "STREET_LIGHT_HUB_12"
]

RESTFUL_ENDPOINTS = [
    "/api/v1/telemetry",
    "/api/v1/control",
    "/auth/login"
]

# Security anomaly patterns
ANOMALY_RATE = 0.05  # 5% chance per log entry
BRUTE_FORCE_THRESHOLD = 10  # Requests per second threshold for anomaly detection
LARGE_PAYLOAD_THRESHOLD = 10000  # 10KB payload threshold for data exfiltration

# --- Helper Functions ---

def generate_valid_ip():
    """Generates a random valid IPv4 address."""
    octets = [str(random.randint(0, 255)) for _ in range(4)]
    return ".".join(octets)

def generate_random_request_method():
    """Returns a random HTTP method from ['GET', 'POST', 'PUT', 'DELETE']."""
    return random.choice(["GET", "POST", "PUT", "DELETE"])

def generate_restful_endpoint():
    """Returns a random RESTful endpoint."""
    return random.choice(RESTFUL_ENDPOINTS)

def generate_anomaly_payload_size():
    """Generates a payload size with potential anomalies."""
    normal = random.randint(100, 5000)  # Normal range
    if random.random() < 0.05:  # 5% chance of large payload
        return random.randint(LARGE_PAYLOAD_THRESHOLD, 20000)
    return normal

def is_anomalous_log(log):
    """Determines if a log entry matches anomaly patterns."""
    # Pattern A: Rapid bursts from single IP hitting /auth/login
    if (log["ip_address"] in ["192.168.1.100", "10.0.0.50"] and  # Example IPs to flag
        log["endpoint"] == "/auth/login" and
        log["processing_time_ms"] < 10.0):
        return True
    
    # Pattern B: Massive payload or high processing time
    if (log["payload_size_bytes"] > LARGE_PAYLOAD_THRESHOLD or
        log["processing_time_ms"] > 150.0):
        return True
    return False

# --- Main Logic ---

def generate_log_batch(size=100):
    """
    Generate a batch of synthetic log entries.
    
    Args:
        size (int): Number of logs to generate
        
    Returns:
        List[Dict]: List of log entries matching Supabase schema
    """
    logs = []
    consecutive_ips = {}  # Track IP frequency for anomaly detection
    
    for _ in range(size):
        # Core log fields
        log = {
            "id": str(uuid.uuid4()),
            "timestamp": (datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))).isoformat(),
            "device_id": random.choice(MUNICIPAL_SYSTEMS),
            "request_method": generate_random_request_method(),
            "endpoint": generate_restful_endpoint(),
            "ip_address": generate_valid_ip(),
            "response_code": random.choice([200] + [404, 500]*2),  # 95% 200, 5% others
            "payload_size_bytes": generate_anomaly_payload_size(),
            "processing_time_ms": round(random.uniform(5.0, 150.0), 1)
        }
        
        # Track IP frequency for anomaly detection
        if log["ip_address"] in consecutive_ips:
            consecutive_ips[log["ip_address"]] += 1
            if consecutive_ips[log["ip_address"]] > BRUTE_FORCE_THRESHOLD:  # 10 requests/sec
                log["anomaly_score"] = round(random.uniform(0.7, 0.95), 2)
                log["model_source"] = "brute_force_model"
                log["risk_level"] = "high"
                log["is_resolved"] = False
        else:
            consecutive_ips[log["ip_address"]] = 1
        
        # Random anomaly injection
        if random.random() < ANOMALY_RATE:
            log["anomaly_score"] = round(random.uniform(0.6, 0.9), 2)
            log["model_source"] = random.choice(["brute_force_model", "exfiltration_model"])
            log["risk_level"] = random.choice(["medium", "high"])
            log["is_resolved"] = False
        else:
            log["anomaly_score"] = 0.0
            log["model_source"] = "baseline_model"
            log["risk_level"] = "low"
            log["is_resolved"] = False
        
        logs.append(log)
    
    return logs

if __name__ == "__main__":
    # Example usage
    batch = generate_log_batch(50)
    print(json.dumps(batch, indent=2))
