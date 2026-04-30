import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

function AngledTick({ x, y, payload }) {
  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0} y={0} dy={8}
        textAnchor="end"
        transform="rotate(-38)"
        fill="#6b7280"
        fontSize={11}
      >
        {payload.value}
      </text>
    </g>
  )
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-sm">
      <p className="font-medium text-gray-800">{label}</p>
      <p className="text-indigo-600 font-semibold">{Number(payload[0].value).toFixed(2)}</p>
    </div>
  )
}

export default function ChannelBarChart({ data, title, loading, domain = [0, 10] }) {
  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        {title && <div className="h-4 w-48 animate-pulse rounded bg-gray-100 mb-4" />}
        <div className="h-72 animate-pulse rounded bg-gray-50" />
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex items-center justify-center h-80">
        <p className="text-gray-400 text-sm">Nessun dato disponibile</p>
      </div>
    )
  }

  const sorted = [...data]
    .filter(d => d.avg != null)
    .sort((a, b) => b.avg - a.avg)

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      {title && (
        <h3 className="text-sm font-semibold text-gray-700 mb-5">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={340}>
        <BarChart data={sorted} margin={{ top: 4, right: 8, bottom: 90, left: -10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis
            dataKey="label"
            tick={<AngledTick />}
            interval={0}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={domain}
            tick={{ fontSize: 11, fill: '#9ca3af' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f9fafb' }} />
          <Bar dataKey="avg" radius={[4, 4, 0, 0]} maxBarSize={40}>
            {sorted.map((_, i) => (
              <Cell
                key={i}
                fill={i === 0 ? '#4f46e5' : i < 3 ? '#818cf8' : '#c7d2fe'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
