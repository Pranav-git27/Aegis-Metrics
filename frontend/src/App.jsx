// File Location: frontend/src/App.jsx
// Aegis Metrics — DevSecOps Telemetry & Threat-Triage Dashboard (Stage 3 UI layer)

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Database,
  ShieldAlert,
  Activity,
  Flame,
  ShieldCheck,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'

import { fetchOverview, fetchActiveAlerts, resolveAlert } from './api.js'
import KpiCard from './KpiCard.jsx'
import AlertsTable from './AlertsTable.jsx'

// Polling cadence (ms). Spec: 3–5s. Using 4s as a balanced default.
const POLL_INTERVAL_MS = 4000

export default function App() {
  // --- Overview metrics ---
  const [overview, setOverview] = useState(null)
  const [overviewError, setOverviewError] = useState(false)

  // --- Active alerts feed ---
  const [alerts, setAlerts] = useState([])
  const [alertsError, setAlertsError] = useState(false)

  // --- Lifecycle / UX state ---
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  // --- Resolve interaction state ---
  const [resolvingIds, setResolvingIds] = useState(() => new Set())
  const [removingIds, setRemovingIds] = useState(() => new Set())

  // Ref so the polling interval always reads the latest mounted flag.
  const mountedRef = useRef(true)
  // Guards against overlapping polls. Without this, a fetch that
  // outlasts the polling cadence stacks a second request on top of it;
  // the two then race to write state, producing the
  // disconnect/reconnect flicker in the feed.
  const isFetchingRef = useRef(false)

  /**
   * Pull both data endpoints. `silent` suppresses the refresh indicator
   * (used by the background polling loop) while the first run shows a
   * loading state.
   */
  const refreshData = useCallback(async (silent = false) => {
    // Skip when a previous poll is still in flight. Overlapping fetches
    // resolve out of order and clobber newer state with stale data,
    // which surfaces as the feed disconnecting then reconnecting.
    if (isFetchingRef.current) return
    isFetchingRef.current = true

    if (!silent) setIsRefreshing(true)

    try {
      const [ov, al] = await Promise.all([
        fetchOverview(),
        fetchActiveAlerts(),
      ])
      if (!mountedRef.current) return

      setOverview(ov)
      setOverviewError(false)
      setAlerts(al)
      setAlertsError(false)
      setLastUpdated(new Date())
    } catch (err) {
      if (!mountedRef.current) return
      // Distinguish which side failed by attempting each independently is
      // overkill; flag both as errored for the robust UX states.
      console.error('[Aegis] telemetry fetch failed:', err)
      setOverviewError(true)
      setAlertsError(true)
    } finally {
      if (mountedRef.current) {
        setIsInitialLoading(false)
        setIsRefreshing(false)
      }
      // Always release the guard so the next tick can proceed — even on
      // failure or unmount (the ref is harmless once unmounted).
      isFetchingRef.current = false
    }
  }, [])

  // Initial load + automated polling interval.
  useEffect(() => {
    mountedRef.current = true
    refreshData(false)

    const intervalId = setInterval(() => {
      refreshData(true)
    }, POLL_INTERVAL_MS)

    return () => {
      mountedRef.current = false
      clearInterval(intervalId)
    }
  }, [refreshData])

  /**
   * Optimistic resolve: fire the PUT, instantly fade the row out, then
   * remove it from local state. On failure, restore the row.
   */
  const handleResolve = useCallback(
    async (alertId) => {
      // Guard against double-clicks / already-in-flight.
      if (resolvingIds.has(alertId) || removingIds.has(alertId)) return

      setResolvingIds((prev) => {
        const next = new Set(prev)
        next.add(alertId)
        return next
      })

      // Kick off the fade-out animation immediately for snappy UX.
      setRemovingIds((prev) => {
        const next = new Set(prev)
        next.add(alertId)
        return next
      })

      try {
        await resolveAlert(alertId)
        if (!mountedRef.current) return

        // Wait for the fade animation to complete before dropping the row,
        // so the removal feels smooth rather than abrupt.
        setTimeout(() => {
          if (!mountedRef.current) return
          setAlerts((prev) => prev.filter((a) => a.alert_id !== alertId))
          setRemovingIds((prev) => {
            const next = new Set(prev)
            next.delete(alertId)
            return next
          })
          setResolvingIds((prev) => {
            const next = new Set(prev)
            next.delete(alertId)
            return next
          })
        }, 400)
      } catch (err) {
        console.error('[Aegis] resolve failed:', err)
        if (!mountedRef.current) return
        // Restore the row — the next poll will reconcile truth.
        setRemovingIds((prev) => {
          const next = new Set(prev)
          next.delete(alertId)
          return next
        })
        setResolvingIds((prev) => {
          const next = new Set(prev)
          next.delete(alertId)
          return next
        })
      }
    },
    [resolvingIds, removingIds],
  )

  // --- Derived display values ---
  const totalLogs = overview?.total_logs ?? 0
  const totalAlerts = overview?.total_alerts ?? 0
  const anomalyRate =
    overview?.anomaly_rate_percentage == null
      ? 0
      : Number(overview.anomaly_rate_percentage)
  const criticalCount = overview?.critical_alerts_count ?? 0

  const formattedAnomaly = Number.isFinite(anomalyRate)
    ? anomalyRate.toFixed(2)
    : '0.00'

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Ambient background glow */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 top-0 h-96 w-96 rounded-full bg-blue-600/10 blur-[120px]" />
        <div className="absolute right-0 top-1/3 h-96 w-96 rounded-full bg-orange-600/10 blur-[120px]" />
        <div className="absolute bottom-0 left-1/2 h-96 w-96 rounded-full bg-emerald-600/5 blur-[120px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* ===== Header ===== */}
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
              onClick={() => refreshData(false)}
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

        {/* ===== Global error banner ===== */}
        {overviewError && !isInitialLoading && (
          <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-800/60 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>
              Live telemetry connection degraded. The dashboard is retrying
              automatically every {POLL_INTERVAL_MS / 1000}s.
            </span>
          </div>
        )}

        {/* ===== KPI Grid ===== */}
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            icon={Database}
            label="Total Logs Ingested"
            value={totalLogs.toLocaleString()}
            accent="blue"
            isLoading={isInitialLoading}
            hint="System-wide log volume"
          />
          <KpiCard
            icon={ShieldAlert}
            label="Security Alerts Flagged"
            value={totalAlerts.toLocaleString()}
            accent="orange"
            isLoading={isInitialLoading}
            hint="Cumulative flagged alerts"
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
            icon={Flame}
            label="Active Critical Incidents"
            value={criticalCount.toLocaleString()}
            accent="red"
            isLoading={isInitialLoading}
            hint="Unresolved critical alerts"
          />
        </section>

        {/* ===== Telemetry Feed ===== */}
        <section className="mt-8">
          <AlertsTable
            alerts={alerts}
            isLoading={isInitialLoading}
            error={alertsError && !isInitialLoading}
            resolvingIds={resolvingIds}
            removingIds={removingIds}
            onResolve={handleResolve}
          />
        </section>

        {/* ===== Footer ===== */}
        <footer className="mt-8 flex items-center justify-between text-xs text-slate-600">
          <span>Aegis Metrics · Stage 3 UI Dashboard</span>
          <span className="font-mono">poll · {POLL_INTERVAL_MS / 1000}s</span>
        </footer>
      </div>
    </div>
  )
}
