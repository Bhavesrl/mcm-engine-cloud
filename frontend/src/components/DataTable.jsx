const PAGE_SIZE = 20

export default function DataTable({
  columns, data, loading, totalCount, page, onPageChange,
}) {
  const totalPages = Math.ceil(totalCount / PAGE_SIZE)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">
          {totalCount.toLocaleString('it-IT')} record totali
        </p>
        {totalPages > 1 && (
          <p className="text-xs text-gray-400">
            Pagina {page + 1} di {totalPages}
          </p>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              {columns.map(col => (
                <th
                  key={col.key}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading
              ? [...Array(10)].map((_, i) => (
                  <tr key={i}>
                    {columns.map(col => (
                      <td key={col.key} className="px-4 py-3">
                        <div className="h-3 animate-pulse rounded bg-gray-100" />
                      </td>
                    ))}
                  </tr>
                ))
              : data.map((row, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    {columns.map(col => (
                      <td
                        key={col.key}
                        className="px-4 py-3 text-gray-700 whitespace-nowrap max-w-[220px] truncate"
                        title={row[col.key] ?? ''}
                      >
                        {row[col.key] ?? <span className="text-gray-300">—</span>}
                      </td>
                    ))}
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page === 0 || loading}
            className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600
                       hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            ← Prec.
          </button>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages - 1 || loading}
            className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 text-gray-600
                       hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Succ. →
          </button>
        </div>
      )}
    </div>
  )
}

export { PAGE_SIZE }
