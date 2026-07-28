-- ========================================================
-- Aegis Metrics / Sentinel-Audit: GNN & Remediation Pipeline Schema
-- ========================================================

-- 1. GNN Threat Logs Table
CREATE TABLE IF NOT EXISTS public.gnn_threat_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT NOT NULL,
    threat_score DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'CRITICAL',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.gnn_threat_logs DISABLE ROW LEVEL SECURITY;

-- 2. Network Policy State Table
CREATE TABLE IF NOT EXISTS public.network_policy_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'NORMAL', -- 'NORMAL', 'QUARANTINED'
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.network_policy_state DISABLE ROW LEVEL SECURITY;

-- 3. GNN Mitigation Actions Audit Table
CREATE TABLE IF NOT EXISTS public.gnn_mitigation_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_name TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    threat_score DOUBLE PRECISION NOT NULL,
    status TEXT NOT NULL DEFAULT 'EXECUTED',
    executed_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.gnn_mitigation_actions DISABLE ROW LEVEL SECURITY;

-- 4. Enable Supabase Realtime Publications
ALTER PUBLICATION supabase_realtime ADD TABLE public.gnn_threat_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE public.gnn_mitigation_actions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.network_policy_state;
```"