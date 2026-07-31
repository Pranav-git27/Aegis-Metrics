import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Database,
  ShieldAlert,
  Activity,
  Lock,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'

import { fetchOverview } from './api.js'
import useSubscription from './useSubscription.js'
import KpiCard from './KpiCard.jsx'
import AlertsTable from './AlertsTable.jsx'
import MitigationsTable from './MitigationsTable.jsx'
import NetworkPolicyGrid from './NetworkPolicyGrid.jsx'

const OVERVIEW_POLL_MS = 5000

export default function App() {
  const [overview, setOverview] = useState(null)
  const [overviewError, setOverviewError] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  const mountedRef = useRef(true)
  const isFetchingRef = useRef(false)

  const {
    data: threats,
    loading: threatsLoading,
    error: threatsError,
  } = useSubscription('gnn_threat_logs', {
    orderBy: { column: 'detected_at', ascending: false },
  })

  const {
    data: mitigations,
    loading: mitigationsLoading,
    error: mitigationsError,
  } = useSubscription('gnn_mitigation_actions', {
    orderBy: { column: 'executed_at', ascending: false },
  })

  const {
    data: devices,
    loading: devicesLoading,
    error: devicesError,
  } = useSubscription('network_policy_state', {
    orderBy: { column: 'device_name', ascending: true },
  })

  const refreshOverview = useCallback(async (silent = false) => {
    if (isFetchingRef.current) return
    isFetchingRef.current = true

    if (!silent) setIsRefreshing(true)

    try {
      const ov = await fetchOverview()
      if (!mountedRef.current) return
      setOverview(ov)
      setOverviewError(false)
      setLastUpdated(new Date())
    } catch (err) {
      if (!mountedRef.current) return
      console.error('[Aegis] overview fetch failed:', err)
      setOverviewError(true)
    } finally {
      if (mountedRef.current) {
        setIsInitialLoading(false)
        setIsRefreshing(false)
      }
      isFetchingRef.current = false
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    refreshOverview(false)

    const intervalId = setInterval(() => {
      refreshOverview(true)
    }, OVERVIEW_POLL_MS)

    return () => {
      mountedRef.current = false
      clearInterval(intervalId)
    }
  }, [refreshOverview])

  const totalLogs = overview?.total_logs ?? 0
  const anomalyRate =
    overview?.anomaly_rate_percentage == null
      ? 0
      : Number(overview.anomaly_rate_percentage)
  const activeThreats = threats.length
  const quarantinedCount = devices.filter(
    (d) => d.status?.toUpperCase() === 'QUARANTINED',
  ).length

  const formattedAnomaly = Number.isFinite(anomalyRate)
    ? anomalyRate.toFixed(2)
    : '0.00'

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 top-0 h-96 w-96 rounded-full bg-blue-600/10 blur-[120px]" />
        <div className="absolute right-0 top-1/3 h-96 w-96 rounded-full bg-orange-600/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/2 h-96 w-96 rounded-full bg-emerald-600/5 blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/20">
              <ShieldCheck className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                Aegis Metrics
              </h1>
              <p className="text-xs text-slate-400">
                DevSecOps Telemetry & Threat-Triage Platform
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-xs text-slate-400 sm:flex">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              {lastUpdated
                ? `Updated ${lastUpdated.toLocaleTimeString()}`
                : 'Awaiting data…'}
            </div>
            <button
              type="button"
              onClick={() => refreshOverview(false)}
              disabled={isRefreshing || isInitialLoading}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/80 px-3.5 py-2 text-xs font-medium text-slate-200 transition-all hover:border-slate-600 hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`}
              />
              Refresh
            </button>
          </div>
        </header>

        {overviewError && !isInitialLoading && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-800/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>
              Overview telemetry connection degraded. Retrying every{' '}
              {OVERVIEW_POLL_MS / 1000}s.
            </span>
          </div>
        )}

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            icon={Database}
            label="Total Telemetry Logs"
            value={totalLogs.toLocaleString()}
            accent="blue"
            isLoading={isInitialLoading}
            hint="System-wide log volume"
          />
          <KpiCard
            icon={ShieldAlert}
            label="Active Threat Detections"
            value={activeThreats.toLocaleString()}
            accent="orange"
            isLoading={isInitialLoading}
            hint="Live GNN threat count"
          />
          <KpiCard
            icon={Activity}
            label="Network Anomaly Rate"
            value={formattedAnomaly}
            suffix="%"
            accent="amber"
            isLoading={isInitialLoading}
            hint="Share of anomalous traffic"
          />
          <KpiCard
            icon={Lock}
            label="Quarantined Devices"
            value={quarantinedCount.toLocaleString()}
            accent="red"
            isLoading={isInitialLoading}
            hint="Devices isolated from the network"
          />
        </section>

        <section className="mt-8 space-y-6">
          <AlertsTable
            threats={threats}
            isLoading={threatsLoading}
            error={threatsError && !threatsLoading}
          />

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
            <MitigationsTable
              mitigations={mitigations}
              isLoading={mitigationsLoading}
              error={mitigationsError && !mitigationsLoading}
            />
            <NetworkPolicyGrid
              devices={devices}
              isLoading={devicesLoading}
              error={devicesError && !devicesLoading}
            />
          </div>
        </section>

        <footer className="mt-8 flex items-center justify-between text-xs text-slate-600">
          <span>Aegis Metrics · Stage 3 UI Dashboard</span>
          <span className="font-mono">supabase · realtime</span>
        </footer>
      </div>
    </div>
  )
}
