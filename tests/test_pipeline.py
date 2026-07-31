"""End-to-end integration tests for the Aegis Metrics defense pipeline.

These tests use the live Supabase project configured in the repository's .env
file. Run them serially; the module-scoped harness preserves one synthetic
packet across all four pipeline stages and removes it when the module ends.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv
from supabase import Client, create_client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from data_pipeline import gnn_extractor  # noqa: E402
from datapipeline.remediation_agent import remediate_threat  # noqa: E402
from models import inference_engine  # noqa: E402

TEST_DEVICE = "TEST_PUMP_99"
THREAT_THRESHOLD = 0.85
DATASET_FILES = (
    PROJECT_ROOT / "models" / "dataset" / "graph.json",
    PROJECT_ROOT / "models" / "dataset" / "node_features.csv",
    PROJECT_ROOT / "models" / "dataset" / "edge_index.csv",
)


class PipelineHarness:
    """Runs each pipeline stage once while exposing its persisted records."""

    def __init__(self, client: Client) -> None:
        self.client = client
        self.log: dict[str, Any] | None = None
        self.threat: dict[str, Any] | None = None
        self.remediated = False
        self.dataset_snapshots = {
            path: path.read_bytes() if path.exists() else None for path in DATASET_FILES
        }

    def cleanup_rows(self) -> None:
        """Delete test data in dependency-safe order."""
        self.client.table("gnn_mitigation_actions").delete().eq(
            "device_name", TEST_DEVICE
        ).execute()
        self.client.table("network_policy_state").delete().eq(
            "device_name", TEST_DEVICE
        ).execute()
        self.client.table("gnn_threat_logs").delete().eq(
            "device_name", TEST_DEVICE
        ).execute()
        # security_alerts rows are removed by their ON DELETE CASCADE relation.
        self.client.table("system_logs").delete().eq(
            "device_id", TEST_DEVICE
        ).execute()

    def restore_dataset(self) -> None:
        """Restore graph artifacts overwritten by the live extraction stage."""
        for path, original_content in self.dataset_snapshots.items():
            if original_content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(original_content)

    def ingest(self) -> dict[str, Any]:
        if self.log is not None:
            return self.log

        packet = {
            "device_id": TEST_DEVICE,
            "request_method": "POST",
            "endpoint": "/api/v1/control",
            "ip_address": "203.0.113.99",
            "response_code": 500,
            "payload_size_bytes": 1_000_000,
            "processing_time_ms": 10_000.0,
        }
        response = self.client.table("system_logs").insert(packet).execute()
        assert response.data, "Supabase did not return the inserted system_logs row"
        self.log = response.data[0]

        # The extractor's fourth feature is the number of unresolved alerts.
        self.client.table("security_alerts").insert(
            {
                "log_id": self.log["id"],
                "anomaly_score": 0.999,
                "model_source": "pytest_synthetic_attack",
                "risk_level": "critical",
                "is_resolved": False,
            }
        ).execute()
        return self.log

    def infer(self) -> dict[str, Any]:
        if self.threat is not None:
            return self.threat

        self.ingest()
        # Rebuild live node features so inference includes TEST_PUMP_99.
        gnn_extractor.supabase = self.client
        inference_engine.supabase = self.client
        gnn_extractor.extract_graph_dataset()
        results = inference_engine.run_gnn_inference()

        local_result = next(
            (row for row in results if row["device_name"] == TEST_DEVICE), None
        )
        assert local_result is not None, (
            f"GNN output did not include synthetic device {TEST_DEVICE}"
        )

        response = (
            self.client.table("gnn_threat_logs")
            .select("*")
            .eq("device_name", TEST_DEVICE)
            .order("detected_at", desc=True)
            .limit(1)
            .execute()
        )
        assert response.data, (
            f"No gnn_threat_logs row was persisted for {TEST_DEVICE}"
        )
        self.threat = response.data[0]
        return self.threat

    def remediate(self) -> dict[str, Any]:
        threat = self.infer()
        if not self.remediated:
            self.remediated = remediate_threat(self.client, threat)

        response = (
            self.client.table("network_policy_state")
            .select("*")
            .eq("device_name", TEST_DEVICE)
            .limit(1)
            .execute()
        )
        assert response.data, (
            f"No network_policy_state row was created for {TEST_DEVICE}"
        )
        return response.data[0]


@pytest.fixture(scope="module")
def pipeline() -> PipelineHarness:
    """Create the live client and always remove synthetic rows after the module."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    missing = [
        name
        for name, value in (("SUPABASE_URL", url), ("Supabase key", key))
        if not value
    ]
    if missing:
        pytest.fail(
            "Missing .env configuration: " + ", ".join(missing),
            pytrace=False,
        )

    harness = PipelineHarness(create_client(url, key))
    harness.cleanup_rows()
    try:
        yield harness
    finally:
        try:
            harness.cleanup_rows()
            print(f"[PASS] Cleanup: removed synthetic rows for {TEST_DEVICE}")
        finally:
            harness.restore_dataset()


def test_anomaly_ingestion(pipeline: PipelineHarness) -> None:
    """Insert and verify one high-risk synthetic packet and its alert features."""
    row = pipeline.ingest()

    assert row["device_id"] == TEST_DEVICE
    assert row["payload_size_bytes"] == 1_000_000
    assert float(row["processing_time_ms"]) == 10_000.0
    print(f"[PASS] Ingestion: high-risk packet stored for {TEST_DEVICE}")


def test_gnn_threat_detection(pipeline: PipelineHarness) -> None:
    """Run live GNN inference and verify its critical persisted assessment."""
    threat = pipeline.infer()
    score = float(threat["threat_score"])

    assert threat["status"] == "CRITICAL", (
        f"Expected CRITICAL GNN status, received {threat['status']!r}"
    )
    assert score > THREAT_THRESHOLD, (
        f"Expected GNN threat_score > {THREAT_THRESHOLD}, received {score:.4f}"
    )
    print(f"[PASS] GNN: {TEST_DEVICE} classified CRITICAL at {score:.4f}")


def test_autonomous_remediation(pipeline: PipelineHarness) -> None:
    """Run the real remediation logic and verify device quarantine state."""
    policy = pipeline.remediate()

    assert pipeline.remediated, "Remediation agent rejected the critical threat"
    assert policy["status"] == "QUARANTINED", (
        f"Expected QUARANTINED policy, received {policy['status']!r}"
    )
    print(f"[PASS] Remediation: {TEST_DEVICE} policy is QUARANTINED")


def test_mitigation_audit_log(pipeline: PipelineHarness) -> None:
    """Verify remediation persisted an executed mitigation audit record."""
    pipeline.remediate()
    response = (
        pipeline.client.table("gnn_mitigation_actions")
        .select("*")
        .eq("device_name", TEST_DEVICE)
        .order("executed_at", desc=True)
        .limit(1)
        .execute()
    )

    assert response.data, (
        f"No gnn_mitigation_actions audit row exists for {TEST_DEVICE}"
    )
    audit = response.data[0]
    assert audit["status"] == "EXECUTED"
    assert float(audit["threat_score"]) > THREAT_THRESHOLD
    assert "quarantined" in audit["action_taken"].lower()
    print(f"[PASS] Audit: mitigation action recorded for {TEST_DEVICE}")
