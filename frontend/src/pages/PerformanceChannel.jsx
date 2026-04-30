import { useState, useEffect, useMemo } from 'react'
import { supabase, avg, fmt, distinct } from '../lib/supabase'
import { PERF_QUALITY_METRICS } from '../lib/constants'
import FilterSelect from '../components/FilterSelect'
import KpiCard from '../components/KpiCard'
import ChannelBarChart from '../components/ChannelBarChart'
import DataTable, { PAGE_SIZE } from '../components/DataTable'

const CHART_COLS = PERF_QUALITY_METRICS.map(c => c.key).join(',')

const TABLE_COLS = [
  { key: 'respondent',                label: 'ID' },
  { key: 's1_specializzazione_medico', label: 'Specializzazione' },
  { key: 'aziende',                   label: 'Azienda' },
  { key: 'area_atc',                  label: 'Area ATC' },
  { key: 'prodotti',                  label: 'Prodotto' },
  { key: 'anno',                      label: 'Anno' },
  { key: 'mese',                      label: 'Mese' },
  { key: 'regione',                   label: 'Regione' },
  { key: 'q16_probabilita_consiglio', label: 'NPS' },
  { key: 'q15_1_chiara',              label: 'Chiarezza' },
]
const TABLE_SELECT = TABLE_COLS.map(c => c.key).join(',')

function buildQuery(base, filters) {
  if (filters.spec)     base = base.eq('s1_specializzazione_medico', filters.spec)
  if (filters.anno)     base = base.eq('anno', Number(filters.anno))
  if (filters.azienda)  base = base.eq('aziende', filters.azienda)
  if (filters.area_atc) base = base.eq('area_atc', filters.area_atc)
  return base
}

export default function PerformanceChannel() {
  const [filters, setFilters]         = useState({ spec: '', anno: '', azienda: '', area_atc: '' })
  const [meta, setMeta]               = useState({ specs: [], anni: [], aziende: [], aree: [] })
  const [metaLoading, setMetaLoading] = useState(true)
  const [rawData, setRawData]         = useState([])
  const [totalCount, setTotalCount]   = useState(0)
  const [chartLoading, setChartLoading] = useState(true)
  const [tableData, setTableData]     = useState([])
  const [tableLoading, setTableLoading] = useState(true)
  const [page, setPage]               = useState(0)
  const [error, setError]             = useState(null)

  // Load filter options once
  useEffect(() => {
    async function loadMeta() {
      setMetaLoading(true)
      const { data, error } = await supabase
        .from('performance_channel')
        .select('s1_specializzazione_medico, anno, aziende, area_atc')
        .limit(10000)

      if (error) { setError(error.message); setMetaLoading(false); return }
      setMeta({
        specs:   distinct(data, 's1_specializzazione_medico'),
        anni:    [...new Set(data.map(r => r.anno))].filter(Boolean).sort((a, b) => b - a).map(String),
        aziende: distinct(data, 'aziende'),
        aree:    distinct(data, 'area_atc'),
      })
      setMetaLoading(false)
    }
    loadMeta()
  }, [])

  // Load count + chart data when filters change
  useEffect(() => {
    let cancelled = false
    async function loadChartData() {
      setChartLoading(true)
      setError(null)

      const [countRes, dataRes] = await Promise.all([
        buildQuery(
          supabase.from('performance_channel').select('respondent', { count: 'exact', head: true }),
          filters
        ),
        buildQuery(
          supabase.from('performance_channel').select(CHART_COLS).limit(10000),
          filters
        ),
      ])

      if (cancelled) return
      if (countRes.error) { setError(countRes.error.message); setChartLoading(false); return }
      if (dataRes.error)  { setError(dataRes.error.message);  setChartLoading(false); return }

      setTotalCount(countRes.count ?? 0)
      setRawData(dataRes.data ?? [])
      setChartLoading(false)
    }

    setPage(0)
    loadChartData()
    return () => { cancelled = true }
  }, [filters])

  // Load table data when page or filters change
  useEffect(() => {
    let cancelled = false
    async function loadTable() {
      setTableLoading(true)
      const from = page * PAGE_SIZE
      const { data, error } = await buildQuery(
        supabase.from('performance_channel').select(TABLE_SELECT).range(from, from + PAGE_SIZE - 1),
        filters
      )
      if (cancelled) return
      if (error) { setError(error.message); setTableLoading(false); return }
      setTableData(data ?? [])
      setTableLoading(false)
    }
    loadTable()
    return () => { cancelled = true }
  }, [page, filters])

  // Derived KPIs
  const kpi = useMemo(() => ({
    avgNps:       avg(rawData, 'q16_probabilita_consiglio'),
    avgChiara:    avg(rawData, 'q15_1_chiara'),
    avgRilevante: avg(rawData, 'q13_1_informazioni_rilevanti'),
    avgCompleta:  avg(rawData, 'q15_4_completa'),
  }), [rawData])

  // Chart data
  const chartData = useMemo(() =>
    PERF_QUALITY_METRICS.map(m => ({
      label: m.label,
      avg:   avg(rawData, m.key),
    })),
    [rawData]
  )

  function setFilter(key, val) {
    setFilters(prev => ({ ...prev, [key]: val }))
  }

  return (
    <div className="space-y-5">
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[160px]">
            <FilterSelect
              label="Specializzazione"
              value={filters.spec}
              onChange={v => setFilter('spec', v)}
              options={meta.specs}
              disabled={metaLoading}
            />
          </div>
          <div className="flex-1 min-w-[160px]">
            <FilterSelect
              label="Azienda"
              value={filters.azienda}
              onChange={v => setFilter('azienda', v)}
              options={meta.aziende}
              disabled={metaLoading}
            />
          </div>
          <div className="flex-1 min-w-[140px]">
            <FilterSelect
              label="Area ATC"
              value={filters.area_atc}
              onChange={v => setFilter('area_atc', v)}
              options={meta.aree}
              disabled={metaLoading}
            />
          </div>
          <div className="w-28">
            <FilterSelect
              label="Anno"
              value={filters.anno}
              onChange={v => setFilter('anno', v)}
              options={meta.anni}
              disabled={metaLoading}
            />
          </div>
          <button
            onClick={() => setFilters({ spec: '', anno: '', azienda: '', area_atc: '' })}
            className="px-4 py-2 text-sm rounded-lg border border-gray-200 text-gray-500
                       hover:bg-gray-50 hover:text-gray-700 transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Record nel campione"
          value={totalCount.toLocaleString('it-IT')}
          badge="n"
          color="indigo"
          loading={chartLoading}
        />
        <KpiCard
          title="Probabilità di Consiglio"
          value={fmt(kpi.avgNps)}
          badge="media /10"
          color="emerald"
          loading={chartLoading}
        />
        <KpiCard
          title="Chiarezza comunicazione"
          value={fmt(kpi.avgChiara)}
          badge="media /10"
          color="amber"
          loading={chartLoading}
        />
        <KpiCard
          title="Completezza"
          value={fmt(kpi.avgCompleta)}
          badge="media /10"
          color="rose"
          loading={chartLoading}
        />
      </div>

      {/* Chart */}
      <ChannelBarChart
        data={chartData}
        title="Qualità della comunicazione (scala 1–10)"
        loading={chartLoading}
        domain={[0, 10]}
      />

      {/* Table */}
      <DataTable
        columns={TABLE_COLS}
        data={tableData}
        loading={tableLoading}
        totalCount={totalCount}
        page={page}
        onPageChange={setPage}
      />
    </div>
  )
}
