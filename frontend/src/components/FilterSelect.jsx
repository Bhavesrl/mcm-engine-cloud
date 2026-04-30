export default function FilterSelect({ label, value, onChange, options, disabled }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
        {label}
      </label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        className="block w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900
                   shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <option value="">Tutti</option>
        {options.map(opt => (
          <option key={opt} value={opt}>{opt}</option>
        ))}
      </select>
    </div>
  )
}
