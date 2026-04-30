const COLORS = {
  indigo: 'text-indigo-600 bg-indigo-50',
  emerald: 'text-emerald-600 bg-emerald-50',
  amber: 'text-amber-600 bg-amber-50',
  rose: 'text-rose-600 bg-rose-50',
}

export default function KpiCard({ title, value, badge, color = 'indigo', loading }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-gray-500 leading-tight">{title}</p>
        {badge && (
          <span className={`shrink-0 rounded-md px-2 py-0.5 text-xs font-semibold ${COLORS[color]}`}>
            {badge}
          </span>
        )}
      </div>
      {loading ? (
        <div className="mt-2 h-9 w-24 animate-pulse rounded bg-gray-100" />
      ) : (
        <p className="mt-2 text-3xl font-bold text-gray-900 tabular-nums">{value}</p>
      )}
    </div>
  )
}
