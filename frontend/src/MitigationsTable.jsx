import { ShieldCheck, Inbox } from 'lucide-react'

const STATUS_BADGE = {
  EXECUTED: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
  FAILED: 'bg-red-500/10 text-red-400 border border-red-500/30',
  PENDING: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
}

export default function MitigationsTable({ mitigations = [], isLoading, error }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="h-5 w-5 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">Autonomous Mitigations Stream</h2>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
            {mitigations.length} actions
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

      <div className="max-h-[24rem] overflow-x-auto overflow-y-auto">
        {isLoading ? (
          <TableSkeleton />
        ) : error ? (
          <ErrorState />
        ) : mitigations.length === 0 ? (
          <EmptyState />
        ) : (
          <table className="w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur">
              <tr className="text-xs uppercase tracking-wider text-slate-500">
                <th className="px-5 py-3 font-medium">Device Name</th>
                <th className="px-5 py-3 font-medium">Action Taken</th>
                <th className="px-5 py-3 font-medium">Threat Score</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Executed At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {mitigations.map((m) => {
                const statusKey = m.status?.toUpperCase()
                const statusStyle = STATUS_BADGE[statusKey] || STATUS_BADGE.EXECUTED
                return (
                  <tr
                    key={m.id}
                    className="animate-fade-in transition-colors hover:bg-slate-800/40"
                  >
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-200">
                      {m.device_name ?? '—'}
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-slate-300">
                      {m.action_taken ?? '—'}
                    </td>
                    <td className="px-5 py-3.5">
                      <span className="font-mono text-xs font-semibold text-slate-200 tabular-nums">
                        {Number(m.threat_score ?? 0).toFixed(4)}
                      </span>
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`inline-flex items-center rounded-md px-2.5 py-1 text-xs font-semibold uppercase tracking-wide ${statusStyle}`}
                      >
                        {statusKey ?? 'EXECUTED'}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 font-mono text-xs text-slate-400">
                      {m.executed_at
                        ? new Date(m.executed_at).toLocaleString()
                        : '—'}
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
      {Array.from({ length: 5 }).map((_, i) => (
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
        <ShieldCheck className="h-6 w-6 text-red-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-red-300">Failed to load mitigations</p>
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
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800/60 ring-1 ring-slate-700">
        <Inbox className="h-6 w-6 text-slate-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-200">No mitigations recorded</p>
        <p className="mt-1 text-xs text-slate-500">
          Autonomous remediation actions will appear here when triggered.
        </p>
      </div>
    </div>
  )
}
