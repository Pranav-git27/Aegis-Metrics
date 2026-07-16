// File Location: frontend/src/AlertsTable.jsx
// Real-time telemetry feed: data grid of active security alerts.

import { CheckCircle2, ShieldAlert, Inbox } from 'lucide-react'

/**
 * Tailwind badge classes keyed by risk_level (lowercased).
 * `critical` uses an animated pulsing red badge per spec.
 */
const RISK_BADGE = {
  critical: 'bg-red-950 text-red-400 border border-red-800 animate-pulse',
  high: 'bg-orange-950 text-orange-400 border border-orange-800',
  medium: 'bg-yellow-950 text-yellow-400 border border-yellow-800',
  low: 'bg-slate-800 text-slate-300 border border-slate-700',
}

/**
 * Resolve a normalized risk level string to a known badge key.
 */
function badgeKey(level) {
  const k = String(level ?? '').toLowerCase()
  return RISK_BADGE[k] ? k : 'low'
}

/**
 * @param {object} props
 * @param {Array} props.alerts - active alert records
 * @param {boolean} props.isLoading - initial loading state
 * @param {boolean} props.error - fetch failure flag
 * @param {Set<string>} props.resolvingIds - alert_ids currently being resolved
 * @param {Set<string>} props.removingIds - alert_ids animating out (fade)
 * @param {(alertId:string)=>void} props.onResolve
 */
export default function AlertsTable({
  alerts,
  isLoading,
  error,
  resolvingIds,
  removingIds,
  onResolve,
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/20 backdrop-blur">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="h-5 w-5 text-orange-400" />
          <h2 className="text-sm font-semibold text-white">Active Threat Feed</h2>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
            {alerts.length} live
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          streaming
        </span>
      </div>

      {/* Body */}
      <div className="max-h-[28rem] overflow-auto">
        {isLoading ? (
          <TableSkeleton />
        ) : error ? (
          <ErrorState />
        ) : alerts.length === 0 ? (
          <EmptyState />
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur">
              <tr className="text-xs uppercase tracking-wider text-slate-500">
                <th className="px-5 py-3 font-medium">Alert ID</th>
                <th className="px-5 py-3 font-medium">Log ID</th>
                <th className="px-5 py-3 font-medium">Risk Level</th>
                <th className="px-5 py-3 font-medium">Anomaly Score</th>
                <th className="px-5 py-3 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {alerts.map((alert) => {
                const id = alert.alert_id
                const isResolving = resolvingIds.has(id)
                const isRemoving = removingIds.has(id)
                const score = Number(alert.anomaly_score ?? 0)
                // anomaly_score is a 0–1 decimal; convert to a 0–100
                // percentage so the progress bar fills proportionally.
                const scorePct = Math.min(100, Math.max(0, score * 100))
                const bk = badgeKey(alert.risk_level)

                return (
                  <tr
                    key={id}
                    className={`group transition-colors hover:bg-slate-800/40 ${
                      isRemoving ? 'animate-fade-out' : 'animate-fade-in'
                    }`}
                  >
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-300">
                      {id}
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-500">
                      {alert.log_id ?? '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${RISK_BADGE[bk]}`}
                      >
                        {alert.risk_level ?? 'unknown'}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-xs font-semibold text-slate-200 tabular-nums">
                          {score.toFixed(2)}
                        </span>
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className={`h-full rounded-full ${
                              bk === 'critical'
                                ? 'bg-red-500'
                                : bk === 'high'
                                  ? 'bg-orange-500'
                                  : bk === 'medium'
                                    ? 'bg-yellow-500'
                                    : 'bg-slate-500'
                            }`}
                            style={{ width: `${scorePct}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => onResolve(id)}
                        disabled={isResolving || isRemoving}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-medium text-slate-200 transition-all hover:border-emerald-600 hover:bg-emerald-600/10 hover:text-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isResolving ? (
                          <>
                            <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" />
                            Resolving
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Resolve
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function TableSkeleton() {
  return (
    <div className="space-y-2 p-5">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="h-12 animate-pulse rounded-lg bg-slate-800/50"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  )
}

function ErrorState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-5 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-950/60 ring-1 ring-red-800">
        <ShieldAlert className="h-6 w-6 text-red-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-red-300">Failed to load threat feed</p>
        <p className="mt-1 text-xs text-slate-500">
          The backend may be unreachable. Retrying automatically…
        </p>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-5 py-16 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-950/60 ring-1 ring-emerald-800">
        <Inbox className="h-6 w-6 text-emerald-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-200">No active alerts</p>
        <p className="mt-1 text-xs text-slate-500">
          All clear. The system is monitoring for new threats.
        </p>
      </div>
    </div>
  )
}
