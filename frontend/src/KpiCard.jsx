// File Location: frontend/src/KpiCard.jsx
// Reusable KPI metric block for the dashboard grid.

/**
 * @param {object} props
 * @param {import('lucide-react').LucideIcon} props.icon - Lucide icon component
 * @param {string} props.label - metric label
 * @param {string|number} props.value - primary metric value
 * @param {string} [props.accent] - tailwind accent color token (e.g. 'blue', 'red')
 * @param {string} [props.suffix] - optional value suffix (e.g. '%')
 * @param {boolean} [props.isLoading] - show skeleton state
 * @param {string} [props.hint] - small descriptive hint under the value
 */
export default function KpiCard({
  icon: Icon,
  label,
  value,
  accent = 'slate',
  suffix = '',
  isLoading = false,
  hint = '',
}) {
  const accentMap = {
    blue: 'from-blue-500/20 to-blue-500/0 text-blue-400 ring-blue-500/20',
    red: 'from-red-500/20 to-red-500/0 text-red-400 ring-red-500/20',
    amber: 'from-amber-500/20 to-amber-500/0 text-amber-400 ring-amber-500/20',
    orange: 'from-orange-500/20 to-orange-500/0 text-orange-400 ring-orange-500/20',
    slate: 'from-slate-500/20 to-slate-500/0 text-slate-300 ring-slate-500/20',
  }

  const accentClasses = accentMap[accent] ?? accentMap.slate

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20 backdrop-blur transition-all duration-300 hover:border-slate-700 hover:shadow-xl hover:shadow-black/30">
      {/* Glow accent */}
      <div
        className={`pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full bg-gradient-to-br ${accentClasses} blur-2xl transition-opacity duration-300 group-hover:opacity-100`}
      />

      <div className="relative flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">
            {label}
          </p>
          <div className="mt-2 flex items-baseline gap-1">
            {isLoading ? (
              <div className="h-8 w-24 animate-pulse rounded-md bg-slate-700/60" />
            ) : (
              <span className="font-mono text-3xl font-bold text-white tabular-nums">
                {value}
                {suffix && <span className="ml-0.5 text-xl font-semibold text-slate-400">{suffix}</span>}
              </span>
            )}
          </div>
          {hint && !isLoading && (
            <p className="mt-1 truncate text-xs text-slate-500">{hint}</p>
          )}
        </div>

        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-800/80 ring-1 ${accentClasses.split(' ').pop()}`}
        >
          {Icon && <Icon className="h-5 w-5" />}
        </div>
      </div>
    </div>
  )
}
