import { Monitor, ShieldAlert, Inbox } from 'lucide-react'

export default function NetworkPolicyGrid({ devices = [], isLoading, error }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg shadow-black/20 backdrop-blur">
      <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
        <div className="flex items-center gap-2.5">
          <Monitor className="h-5 w-5 text-cyan-400" />
          <h2 className="text-sm font-semibold text-white">Network Policy & Topology</h2>
          <span className="rounded-full bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">
            {devices.length} devices
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

      {isLoading ? (
        <GridSkeleton />
      ) : error ? (
        <ErrorState />
      ) : devices.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-2 max-h-[400px] overflow-y-auto">
          {devices.map((d) => (
            <div
              key={d.id || d.device_name}
              className="flex flex-col justify-between p-3.5 bg-slate-900/90 border border-red-500/30 rounded-xl shadow-md min-w-0"
            >
              {/* Top Row: Icon + Name */}
              <div className="flex items-center gap-2 mb-3 min-w-0">
                <ShieldAlert className="w-4 h-4 text-red-400 shrink-0" />
                <span
                  className="text-xs font-semibold text-slate-100 truncate tracking-wide"
                  title={d.device_name}
                >
                  {d.device_name}
                </span>
              </div>

              {/* Bottom Row: Badge on Left, Time on Right */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px] mt-1">
                <span
                  className={`px-2 py-0.5 rounded font-mono text-[10px] uppercase font-bold tracking-wider ${
                    d.status === 'QUARANTINED'
                      ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                      : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                  }`}
                >
                  {d.status}
                </span>
                <span className="text-slate-400 font-mono text-[10px] shrink-0 ml-2">
                  {d.updated_at
                    ? new Date(d.updated_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })
                    : 'LIVE'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-2 max-h-[400px] overflow-y-auto">
      {Array.from({ length: 4 }).map((_, i) => (
        <div
          key={i}
          className="h-24 animate-pulse rounded-xl bg-slate-800/50"
          style={{ animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  )
}

function ErrorState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-5 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-950/60 ring-1 ring-red-800">
        <Monitor className="h-6 w-6 text-red-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-red-300">Failed to load network topology</p>
        <p className="mt-1 text-xs text-slate-500">
          Supabase Realtime connection degraded. Retrying…
        </p>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-5 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-800/60 ring-1 ring-slate-700">
        <Inbox className="h-6 w-6 text-slate-400" />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-200">No devices registered</p>
        <p className="mt-1 text-xs text-slate-500">
          Network policy state will populate as devices are discovered.
        </p>
      </div>
    </div>
  )
}
