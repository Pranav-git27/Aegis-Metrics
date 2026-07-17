# File Location: data_pipeline/gnn_extractor.py
"""
GNN data extractor for Stage 4 (Spatio-Temporal GNN Data Preparation).

Pulls every row from the `system_logs` and `security_alerts` Supabase tables,
collapses them into a static spatial graph snapshot, and serializes the
structural arrays (node index map, COO edge_index, per-node feature matrix)
to `models/dataset/` as both JSON and CSV so the artifacts can be dragged
straight into a Google Colab notebook for PyTorch Geometric training.

Graph definition
-----------------
* Nodes  : one per unique device name (index 0 .. N-1).
* Edges  : derived from `DEVICE_CONNECTIONS` in `data_pipeline/bulk_injector.py`
           (directed src -> tgt, COO format).
* Features per node (4-dim vector):
    0. total_logs            - count of system_logs rows for the device
    1. avg_processing_time_ms - mean processing_time_ms across those logs
    2. avg_payload_size_bytes - mean payload_size_bytes across those logs
    3. total_active_alerts    - count of unresolved security_alerts linked
                               to the device via system_logs.log_id
"""
import os
import sys
import json
import logging
from collections import defaultdict

# Make the project root importable so `backend` / `data_pipeline` resolve
# regardless of the current working directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from backend.supabase_client import supabase  # module-level client (may be None)
from data_pipeline.bulk_injector import DEVICE_CONNECTIONS

# --- Configuration -----------------------------------------------------------
# Supabase/PostgREST caps each response at 1000 rows; we page past that limit.
PAGE_SIZE = 1000
OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "models", "dataset")

# Columns we actually need -> keep the wire payload small even at 15k+ rows.
LOG_COLUMNS = "id,device_id,processing_time_ms,payload_size_bytes"
ALERT_COLUMNS = "log_id,is_resolved"

# The ordered feature names for the per-node vector. Keep this in sync with
# compute_node_features() so the JSON/CSV stay self-describing.
FEATURE_NAMES = [
    "total_logs",
    "avg_processing_time_ms",
    "avg_payload_size_bytes",
    "total_active_alerts",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# --- Supabase fetch helpers -------------------------------------------------
def _fetch_all_rows(table_name: str, select: str) -> list:
    """
    Page through every row of a Supabase table using inclusive `.range()`.

    PostgREST returns at most 1000 rows per request, so we slide a window of
    PAGE_SIZE rows until we either exhaust the `count` header (preferred) or
    receive a short page (fallback when count is unavailable).

    Args:
        table_name: Target table (e.g. "system_logs").
        select:     Comma-separated column list for the `.select()` clause.

    Returns:
        list[dict]: All rows for the table, concatenated in insertion order.
    """
    if supabase is None:
        raise RuntimeError(
            "Supabase client is not initialized. Check SUPABASE_URL / "
            "SUPABASE_KEY in your .env before running the extractor."
        )

    rows: list = []
    start = 0
    total = None

    while True:
        end = start + PAGE_SIZE - 1  # .range() is inclusive on both ends
        response = (
            supabase.table(table_name)
            .select(select, count="exact")
            .range(start, end)
            .execute()
        )

        page = response.data or []
        rows.extend(page)

        # Prefer the exact count header when PostgREST returns it.
        if total is None:
            total = getattr(response, "count", None)

        if total is not None:
            if len(rows) >= total:
                break
        elif len(page) < PAGE_SIZE:
            # No count header -> a short page means we've reached the end.
            break

        start += PAGE_SIZE

    logger.info(f"Fetched {len(rows)} rows from '{table_name}'.")
    return rows


def fetch_system_logs() -> list:
    """Return every system_logs row (only the columns the GNN needs)."""
    return _fetch_all_rows("system_logs", LOG_COLUMNS)


def fetch_security_alerts() -> list:
    """Return every security_alerts row (only log_id + is_resolved)."""
    return _fetch_all_rows("security_alerts", ALERT_COLUMNS)


# --- Graph construction ------------------------------------------------------
def build_device_index_map(logs: list) -> dict:
    """
    Map every unique device name to a stable integer index 0..N-1.

    The node set is the union of:
      * device_ids observed in `system_logs` (the live data), and
      * every device referenced in `DEVICE_CONNECTIONS` (the declared
        topology) so the edge_index never references a missing node even if
        a device has zero logs in the current snapshot.

    Indices are assigned in sorted-name order for deterministic, reproducible
    output across runs.
    """
    device_names = set()
    for log in logs:
        device_id = log.get("device_id")
        if device_id:
            device_names.add(device_id)

    for src, targets in DEVICE_CONNECTIONS.items():
        device_names.add(src)
        device_names.update(targets)

    return {name: idx for idx, name in enumerate(sorted(device_names))}


def build_edge_index(device_index_map: dict) -> dict:
    """
    Build the directed spatial graph topology in COO format.

    For every (src -> tgt) pair declared in `DEVICE_CONNECTIONS` we emit one
    directed edge. The result is returned as two parallel index lists so it
    maps 1:1 onto `torch.tensor([sources, targets])` (shape 2 x E) in PyG.

    Returns:
        dict with:
          * "edge_index" : [[src...], [tgt...]]  (2 x E, COO / row-pair form)
          * "edges"      : [[src, tgt], ...]      (E x 2, human-readable pairs)
          * "num_edges"  : int
    """
    sources, targets, pairs = [], [], []

    for src_device, connected in DEVICE_CONNECTIONS.items():
        if src_device not in device_index_map:
            logger.warning(f"Edge source '{src_device}' missing from index map; skipping.")
            continue
        src_idx = device_index_map[src_device]

        for tgt_device in connected:
            if tgt_device not in device_index_map:
                logger.warning(f"Edge target '{tgt_device}' missing from index map; skipping.")
                continue
            tgt_idx = device_index_map[tgt_device]

            sources.append(src_idx)
            targets.append(tgt_idx)
            pairs.append([src_idx, tgt_idx])

    return {
        "edge_index": [sources, targets],  # 2 x E
        "edges": pairs,                    # E x 2
        "num_edges": len(pairs),
    }


# --- Feature engineering -----------------------------------------------------
def compute_node_features(logs: list, alerts: list, device_index_map: dict) -> list:
    """
    Compute the 4-dim feature vector for every device node.

    Feature order (matches FEATURE_NAMES):
        0. total_logs
        1. avg_processing_time_ms
        2. avg_payload_size_bytes
        3. total_active_alerts   (security_alerts with is_resolved == False,
           joined to the device via system_logs.id == security_alerts.log_id)

    Returns:
        list[list[float]]: N x 4 matrix aligned with device_index_map indices.
    """
    n = len(device_index_map)

    log_counts = defaultdict(int)
    proc_time_sum = defaultdict(float)
    proc_time_n = defaultdict(int)
    payload_sum = defaultdict(float)
    payload_n = defaultdict(int)

    # log_id -> device_id lookup so alerts can be attributed to a device.
    log_id_to_device = {}

    for log in logs:
        device_id = log.get("device_id")
        log_id = log.get("id")
        if log_id:
            log_id_to_device[log_id] = device_id

        if device_id is None:
            continue
        log_counts[device_id] += 1

        proc = log.get("processing_time_ms")
        if proc is not None:
            proc_time_sum[device_id] += float(proc)
            proc_time_n[device_id] += 1

        payload = log.get("payload_size_bytes")
        if payload is not None:
            payload_sum[device_id] += float(payload)
            payload_n[device_id] += 1

    # Active (unresolved) alert counts per device.
    active_alert_counts = defaultdict(int)
    for alert in alerts:
        if alert.get("is_resolved"):
            continue  # only unresolved alerts count as "active"
        device_id = log_id_to_device.get(alert.get("log_id"))
        if device_id is not None:
            active_alert_counts[device_id] += 1

    # Assemble the N x 4 matrix in index order.
    index_to_name = {idx: name for name, idx in device_index_map.items()}
    features = []
    for idx in range(n):
        name = index_to_name[idx]
        total_logs = log_counts.get(name, 0)
        avg_proc = (proc_time_sum[name] / proc_time_n[name]) if proc_time_n[name] else 0.0
        avg_payload = (payload_sum[name] / payload_n[name]) if payload_n[name] else 0.0
        active_alerts = active_alert_counts.get(name, 0)
        features.append([total_logs, avg_proc, avg_payload, active_alerts])

    return features


# --- Serialization -----------------------------------------------------------
def save_outputs(device_index_map: dict, edge_index: dict, node_features: list,
                 output_dir: str = OUTPUT_DIR) -> dict:
    """
    Write the graph artifacts to `output_dir` as JSON + CSV.

    Files produced:
        * graph.json          - full structural payload (index map, edge_index,
                                node_features, feature_names, metadata)
        * node_features.csv   - one row per device with its 4 features
        * edge_index.csv      - one row per directed edge (source,target)

    Returns:
        dict of absolute file paths written.
    """
    os.makedirs(output_dir, exist_ok=True)

    graph_payload = {
        "description": "Spatial graph snapshot for PyTorch Geometric GNN training.",
        "feature_names": FEATURE_NAMES,
        "num_nodes": len(device_index_map),
        "device_index_map": device_index_map,
        "edge_index": edge_index["edge_index"],   # 2 x E (COO)
        "num_edges": edge_index["num_edges"],
        "node_features": node_features,           # N x 4
        "metadata": {
            "topology_source": "data_pipeline.bulk_injector.DEVICE_CONNECTIONS",
            "edge_format": "COO - edge_index[0]=sources, edge_index[1]=targets",
            "feature_order": FEATURE_NAMES,
        },
    }

    json_path = os.path.join(output_dir, "graph.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(graph_payload, fh, indent=2)

    # node_features.csv: device_name, device_index, <4 feature columns>
    nodes_csv_path = os.path.join(output_dir, "node_features.csv")
    with open(nodes_csv_path, "w", encoding="utf-8") as fh:
        header = ["device_name", "device_index"] + FEATURE_NAMES
        fh.write(",".join(header) + "\n")
        for idx in range(len(device_index_map)):
            name = {v: k for k, v in device_index_map.items()}[idx]
            row = [name, idx] + [str(v) for v in node_features[idx]]
            fh.write(",".join(str(c) for c in row) + "\n")

    # edge_index.csv: source_index, target_index
    edges_csv_path = os.path.join(output_dir, "edge_index.csv")
    with open(edges_csv_path, "w", encoding="utf-8") as fh:
        fh.write("source_index,target_index\n")
        for src_idx, tgt_idx in edge_index["edges"]:
            fh.write(f"{src_idx},{tgt_idx}\n")

    return {
        "graph_json": json_path,
        "node_features_csv": nodes_csv_path,
        "edge_index_csv": edges_csv_path,
    }


# --- Orchestration -----------------------------------------------------------
def extract_graph_dataset() -> dict:
    """
    End-to-end extraction: fetch -> index -> topology -> features -> save.

    Returns:
        dict summarizing the produced graph (counts + output file paths).
    """
    logger.info("Stage 4 GNN data extraction starting.")

    logs = fetch_system_logs()
    alerts = fetch_security_alerts()

    device_index_map = build_device_index_map(logs)
    logger.info(f"Mapped {len(device_index_map)} unique devices to indices 0..{len(device_index_map) - 1}.")

    edge_index = build_edge_index(device_index_map)
    logger.info(f"Built edge_index (COO) with {edge_index['num_edges']} directed edges.")

    node_features = compute_node_features(logs, alerts, device_index_map)
    logger.info(f"Computed {len(node_features)} x {len(FEATURE_NAMES)} node feature matrix.")

    paths = save_outputs(device_index_map, edge_index, node_features)

    summary = {
        "num_nodes": len(device_index_map),
        "num_edges": edge_index["num_edges"],
        "num_logs": len(logs),
        "num_alerts": len(alerts),
        "feature_dim": len(FEATURE_NAMES),
        "output_files": paths,
    }

    logger.info("=" * 60)
    logger.info("GNN DATASET EXTRACTION COMPLETE")
    logger.info(f"Nodes : {summary['num_nodes']}")
    logger.info(f"Edges : {summary['num_edges']}")
    logger.info(f"Logs  : {summary['num_logs']}")
    logger.info(f"Alerts: {summary['num_alerts']}")
    logger.info(f"Saved : {paths['graph_json']}")
    logger.info(f"       {paths['node_features_csv']}")
    logger.info(f"       {paths['edge_index_csv']}")
    logger.info("=" * 60)

    return summary


if __name__ == "__main__":
    try:
        extract_graph_dataset()
    except Exception as exc:
        logger.error(f"GNN dataset extraction failed: {exc}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
