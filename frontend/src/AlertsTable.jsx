import { ShieldAlert, Inbox } from 'lucide-react'

const RISK_BADGE = {
  critical: 'bg-red-950 text-red-400 border border-red-800 animate-pulse',
  high: 'bg-orange-950 text-orange-400 border border-orange-800',
  medium: 'bg-yellow-950 text-yellow-400 border border-yellow-800',
  low: 'bg-slate-800 text-slate-300 border border-slate-700',
}

const STATUS_BADGE = {
  CRITICAL: 'bg-red-500/10 text-red-400 border border-red-500/30',
  QUARANTINED: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
  HEALTHY: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
}

function riskLevel(score) {
  if (score >= 0.8) return 'critical'
  if (score >= 0.5) return 'high'
  if (score >= 0.2) return 'medium'
  return 'low'
}

export default function AlertsTable({ threats = [], isLoading, error }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <ShieldAlert className="h-5 w-5 text-orange-400" />
          <h2 className="text-sm font-semibold text-white">Active Threat Feed</h2>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
            {threats.length} live
          </span>
        </div>
        <span className="flex items-center gap-1.5 text-xs text-slate-500">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
          </span>
          realtime
        </span>
      </div>

      <div className="max-h-[28rem] overflow-auto">
        {isLoading ? (
          <TableSkeleton />
        ) : error ? (
          <ErrorState />
        ) : threats.length === 0 ? (
          <EmptyState />
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur">
              <tr className="text-xs uppercase tracking-wider text-slate-500">
                <th className="px-5 py-3 font-medium">Threat ID</th>
                <th className="px-5 py-3 font-medium">Device Name</th>
                <th className="px-5 py-3 font-medium">Risk Level</th>
                <th className="px-5 py-3 font-medium">Threat Score</th>
                <th className="px-5 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {threats.map((t) => {
                const risk = riskLevel(t.threat_score)
                const statusKey = t.status?.toUpperCase()
                const statusStyle = STATUS_BADGE[statusKey] || STATUS_BADGE.CRITICAL
                return (
                  <tr
                    key={t.id}
                    className="animate-fade-in transition-colors hover:bg-slate-800/40"
                  >
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-300">
                      {t.id?.slice(0, 8)}…
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-200">
                      {t.device_name ?? '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${RISK_BADGE[risk]}`}
                      >
                        {risk}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-xs font-semibold text-slate-200 tabular-nums">
                          {Number(t.threat_score ?? 0).toFixed(4)}
                        </span>
                        <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-800">
                          <div
                            className={`h-full rounded-full ${
                              risk === 'critical'
                                ? 'bg-red-500'
                                : risk === 'high'
                                  ? 'bg-orange-500'
                                  : risk === 'medium'
                                    ? 'bg-yellow-500'
                                    : 'bg-slate-500'
                            }`}
                            style={{ width: `${Math.min(100, (t.threat_score ?? 0) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${statusStyle}`}
                      >
                        {statusKey ?? 'CRITICAL'}
                      </span>
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
          Supabase Realtime connection degraded. Retrying…
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
        <p className="text-sm font-semibold text-slate-200">No active threats</p>
        <p className="mt-1 text-xs text-slate-500">
          All clear. The GNN model is monitoring for new anomalies.
        </p>
      </div>
    </div>
  )
}
