import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import pandas as pd
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv, GATConv

# ---------------------------------------------------------
# 1. MODEL ARCHITECTURE DEFINITION
# (Matches the trained Colab ThreatGNN network exactly)
# ---------------------------------------------------------
class ThreatGNN(nn.Module):
    def __init__(self, in_features, hidden_dim, num_classes):
        super(ThreatGNN, self).__init__()
        self.gcn = GCNConv(in_features, hidden_dim)
        self.gat = GATConv(hidden_dim, hidden_dim, heads=2, concat=False)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self.dropout = nn.Dropout(p=0.2)

    def forward(self, x, edge_index):
        h = self.gcn(x, edge_index)
        h = F.relu(h)
        h = self.dropout(h)
        
        h = self.gat(h, edge_index)
        h = F.relu(h)
        
        out = self.classifier(h)
        return out

# ---------------------------------------------------------
# 2. INFERENCE RUNNER
# ---------------------------------------------------------
def run_gnn_inference():
    print("🚀 Initializing Live GNN Inference Engine...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "gnn_threat_model.pt")
    features_path = os.path.join(base_dir, "dataset", "node_features.csv")
    edges_path = os.path.join(base_dir, "dataset", "edge_index.csv")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"❌ Model file not found at {model_path}. Did you move gnn_threat_model.pt into models/?")

    # 1. Load Data
    df_features = pd.read_csv(features_path)
    df_edges = pd.read_csv(edges_path)

    feature_cols = ["total_logs", "avg_processing_time_ms", "avg_payload_size_bytes", "total_active_alerts"]
    x_tensor = torch.tensor(df_features[feature_cols].values, dtype=torch.float)
    edge_index_tensor = torch.tensor(df_edges[["source_index", "target_index"]].values.T, dtype=torch.long)

    graph_data = Data(x=x_tensor, edge_index=edge_index_tensor)

    # 2. Load Model & Weights
    model = ThreatGNN(in_features=4, hidden_dim=16, num_classes=2)
    model.load_state_dict(torch.load(model_path))
    model.eval()  # Set to evaluation mode (disables dropout)

    # 3. Compute Real-Time Predictions
    with torch.no_grad():
        logits = model(graph_data.x, graph_data.edge_index)
        probabilities = F.softmax(logits, dim=1)  # Convert raw logits to 0.0 - 1.0 confidence
        threat_scores = probabilities[:, 1].tolist() # Probability of class 1 (High Risk)

    # 4. Generate Risk Report
    results = []
    print("\n=======================================================")
    print("      LIVE SMART CITY GNN THREAT ASSESSMENT RESULTS    ")
    print("=======================================================")
    
    for idx, row in df_features.iterrows():
        device_name = row["device_name"]
        score = threat_scores[idx]
        status = "CRITICAL / COMPROMISED ⚠️" if score >= 0.5 else "HEALTHY / SAFE ✅"
        
        results.append({
            "device_name": device_name,
            "threat_score": round(score, 4),
            "status": status
        })
        
        print(f"[{status}] {device_name:<25} | Threat Confidence: {score*100:6.2f}%")

    print("=======================================================\n")
    return results

if __name__ == "__main__":
    run_gnn_inference()