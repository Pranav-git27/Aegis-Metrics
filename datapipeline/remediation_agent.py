"""Automated remediation agent for high-risk GNN threat records.

The agent polls ``gnn_threat_logs`` and applies a defense protocol whenever a
record has a threat score greater than or equal to ``THREAT_THRESHOLD``:

* set the device's ``network_policy_state`` row to ``QUARANTINED``;
* emit a structured remediation log describing lateral-movement containment;
* insert an audit row into ``gnn_mitigation_actions``.

Run this module directly for continuous polling, or import and call
``process_pending_threats`` from an existing scheduler/worker.
"""

from __future__ import annotations

import argparse
import logging
import os
import time
from typing import Any, Iterable

from dotenv import load_dotenv
from supabase import Client, create_client

THREAT_THRESHOLD = 0.80
DEFAULT_POLL_INTERVAL_SECONDS = 10.0
THREAT_LOGS_TABLE = "gnn_threat_logs"
NETWORK_POLICY_TABLE = "network_policy_state"
MITIGATION_ACTIONS_TABLE = "gnn_mitigation_actions"
QUARANTINE_STATE = "QUARANTINED"
ACTION_TAKEN = (
    "Automated defense protocol: device quarantined; lateral movement "
    "contained by isolating the device from the network."
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("remediation_agent")


def create_supabase_client() -> Client:
    """Create a privileged Supabase client from environment variables."""
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    missing = [
        name
        for name, value in (
            ("SUPABASE_URL", url),
            ("SUPABASE_SERVICE_ROLE_KEY", service_role_key),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): " + ", ".join(missing)
        )

    return create_client(url, service_role_key)


def _device_name(record: dict[str, Any]) -> str:
    """Extract and validate the device identifier from a threat record."""
    device_name = record.get("device_name") or record.get("device_id")
    if not device_name:
        raise ValueError("Threat record does not contain device_name or device_id")
    return str(device_name)


def _threat_score(record: dict[str, Any]) -> float:
    """Extract and validate the numeric threat score from a threat record."""
    value = record.get("threat_score")
    if value is None:
        raise ValueError("Threat record does not contain threat_score")
    return float(value)


def quarantine_device(client: Client, device_name: str) -> None:
    """Create or update a device policy with a QUARANTINED status."""
    client.table(NETWORK_POLICY_TABLE).upsert(
        {"device_name": device_name, "status": QUARANTINE_STATE},
        on_conflict="device_name",
    ).execute()


def generate_remediation_log(device_name: str, threat_score: float) -> None:
    """Emit the automated security remediation event to application logs."""
    logger.warning(
        "SECURITY_REMEDIATION device_name=%s threat_score=%.4f "
        "policy_state=%s containment=lateral_movement_blocked details=%s",
        device_name,
        threat_score,
        QUARANTINE_STATE,
        ACTION_TAKEN,
    )


def insert_mitigation_audit(
    client: Client, device_name: str, threat_score: float
) -> None:
    """Persist the required mitigation action audit row."""
    client.table(MITIGATION_ACTIONS_TABLE).insert(
        {
            "device_name": device_name,
            "action_taken": ACTION_TAKEN,
            "threat_score": threat_score,
        }
    ).execute()


def remediate_threat(client: Client, record: dict[str, Any]) -> bool:
    """Apply the defense protocol to one qualifying threat record.

    Returns ``True`` when remediation was applied and ``False`` when the record
    was below the configured threshold.
    """
    score = _threat_score(record)
    if score < THREAT_THRESHOLD:
        return False

    device_name = _device_name(record)
    quarantine_device(client, device_name)
    generate_remediation_log(device_name, score)
    insert_mitigation_audit(client, device_name, score)
    logger.info("Automated defense protocol completed for device %s", device_name)
    return True


def process_records(client: Client, records: Iterable[dict[str, Any]]) -> int:
    """Process supplied records and return the number successfully remediated."""
    remediated = 0
    for record in records:
        try:
            if remediate_threat(client, record):
                remediated += 1
        except (TypeError, ValueError) as exc:
            logger.error("Skipping invalid threat record %r: %s", record, exc)
        except Exception:
            logger.exception("Defense protocol failed for threat record %r", record)
    return remediated


def fetch_qualifying_threats(client: Client) -> list[dict[str, Any]]:
    """Fetch threat rows at or above the automated-remediation threshold."""
    response = (
        client.table(THREAT_LOGS_TABLE)
        .select("*")
        .gte("threat_score", THREAT_THRESHOLD)
        .execute()
    )
    return response.data or []


def process_pending_threats(client: Client) -> int:
    """Fetch and process the current qualifying records once."""
    records = fetch_qualifying_threats(client)
    logger.info("Fetched %d qualifying threat record(s)", len(records))
    return process_records(client, records)


def run_polling_agent(client: Client, poll_interval: float) -> None:
    """Continuously poll for threats, processing each record once per process."""
    processed_record_ids: set[str] = set()
    logger.info(
        "Remediation agent listening to %s every %.1f seconds",
        THREAT_LOGS_TABLE,
        poll_interval,
    )

    try:
        while True:
            try:
                records = fetch_qualifying_threats(client)
                new_records: list[dict[str, Any]] = []

                for record in records:
                    record_id = record.get("id")
                    if record_id is None:
                        # Without a stable ID, process the row but do not claim durable
                        # deduplication; the source table should ideally expose an id.
                        new_records.append(record)
                        continue

                    record_key = str(record_id)
                    if record_key not in processed_record_ids:
                        new_records.append(record)
                        processed_record_ids.add(record_key)

                process_records(client, new_records)
            except Exception:
                logger.exception("Failed to poll %s; retrying", THREAT_LOGS_TABLE)

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        logger.info("\n[INFO] Remediation agent shut down gracefully.")


def main() -> None:
    """Command-line entry point for one-shot or continuous processing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process currently qualifying records once and exit.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help="Seconds between polling cycles (default: 10).",
    )
    args = parser.parse_args()

    if args.poll_interval <= 0:
        parser.error("--poll-interval must be greater than zero")

    client = create_supabase_client()
    if args.once:
        process_pending_threats(client)
    else:
        run_polling_agent(client, args.poll_interval)


if __name__ == "__main__":
    main()
