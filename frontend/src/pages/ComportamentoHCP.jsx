import { useState, useEffect, useMemo } from 'react'
import { supabase, avg, fmt, distinct } from '../lib/supabase'
import { HCP_UTILITY_CHANNELS } from '../lib/constants'
import FilterSelect from '../components/FilterSelect'
import KpiCard from '../components/KpiCard'
import ChannelBarChart from '../components/ChannelBarChart'
import DataTable, { PAGE_SIZE } from '../components/DataTable'

const CHART_COLS = HCP_UTILITY_CHANNELS.map(c => c.key).join(',')

const TABLE_COLS = [
  { key: 'respondent',                                    label: 'ID' },
  { key: 'sprcializzazione_del_medico_s1',                label: 'Specializzazione' },
  { key: 'anno',                                          label: 'Anno' },
  { key: 'mese',                                          label: 'Mese' },
  { key: 'regione',                                       label: 'Regione' },
  { key: 'area_nielsen',                                  label: 'Area Nielsen' },
  { key: 'q24_generazione',                              label: 'Generazione' },
  { key: 'tipo_specializzazione_primary_secondary_care',  label: 'Tipo' },
]
const TABLE_SELECT = TABLE_COLS.map(c => c.key).join(',')

function buildQuery(base, filters) {
  if (filters.spec)    base = base.eq('sprcializzazione_del_medico_s1', filters.spec)
  if (filters.anno)    base = base.eq('anno', Number(filters.anno))
  if (filters.regione) base = base.eq('regione', filters.regione)
  return base
}

export default function ComportamentoHCP() {
  const [filters, setFilters]       = useState({ spec: '', anno: '', regione: '' })
  const [meta, setMeta]             = useState({ specs: [], anni: [], regioni: [] })
  const [metaLoading, setMetaLoading] = useState(true)
  const [rawData, setRawData]       = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [chartLoading, setChartLoading] = useState(true)
  const [tableData, setTableData]   = useState([])
  const [tableLoading, setTableLoading] = useState(true)
  const [page, setPage]             = useState(0)
  const [error, setError]           = useState(null)

  // Load filter options once on mount
  useEffect(() => {
    async function loadMeta() {
      setMetaLoading(true)
      const { data, error } = await supabase
        .from('comportamento_hcp')
        .select('sprcializzazione_del_medico_s1, anno, regione')
        .limit(8000)

      if (error) { setError(error.message); setMetaLoading(false); return }
      setMeta({
        specs:   distinct(data, 'sprcializzazione_del_medico_s1'),
        anni:    [...new Set(data.map(r => r.anno))].filter(Boolean).sort((a, b) => b - a).map(String),
        regioni: distinct(data, 'regione'),
      })
      setMetaLoading(false)
    }
    loadMeta()
  }, [])

  // Load count + chart/KPI data when filters change
  useEffect(() => {
    let cancelled = false
    async function loadChartData() {
      setChartLoading(true)
      setError(null)

      const [countRes, dataRes] = await Promise.all([
        buildQuery(
          supabase.from('comportamento_hcp').select('respondent', { count: 'exact', head: true }),
          filters
        ),
        buildQuery(
          supabase.from('comportamento_hcp').select(CHART_COLS).limit(10000),
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
        supabase.from('comportamento_hcp').select(TABLE_SELECT).range(from, from + PAGE_SIZE - 1),
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

  // Derived KPIs from raw data
  const kpi = useMemo(() => ({
    avgFtof:     avg(rawData, 'q6_2_utilita_ftof'),
    avgWebinar:  avg(rawData, 'q6_17_utilita_webinar'),
    avgDigitale: avg(rawData.map(r => {
      const vals = [
        r.q6_4_utilita_isf_webcall,
        r.q6_12_utilita_sito_web_di_prodotto,
        r.q6_14_utilita_social_network,
        r.q6_17_utilita_webinar,
        r.q6_18_utilita_fad_on_line,
      ].filter(v => v != null)
      return vals.length ? { v: vals.reduce((a, b) => a + b, 0) / vals.length } : { v: null }
    }), 'v'),
  }), [rawData])

  // Chart data from raw data
  const chartData = useMemo(() =>
    HCP_UTILITY_CHANNELS.map(ch => ({
      label: ch.label,
      avg:   avg(rawData, ch.key),
    })),
    [rawData]
  )

  function setFilter(key, val) {
    setFilters(prev => ({ ...prev, [key]: val }))
  }

  return (
    <div className="space-y-5">
      {/* Error banner */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 min-w-[180px]">
            <FilterSelect
              label="Specializzazione"
              value={filters.spec}
              onChange={v => setFilter('spec', v)}
              options={meta.specs}
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
          <div className="flex-1 min-w-[180px]">
            <FilterSelect
              label="Regione"
              value={filters.regione}
              onChange={v => setFilter('regione', v)}
              options={meta.regioni}
              disabled={metaLoading}
            />
          </div>
          <button
            onClick={() => setFilters({ spec: '', anno: '', regione: '' })}
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
          title="HCP nel campione"
          value={totalCount.toLocaleString('it-IT')}
          badge="n"
          color="indigo"
          loading={chartLoading}
        />
        <KpiCard
          title="Utilità ISF F2F"
          value={fmt(kpi.avgFtof)}
          badge="media /10"
          color="emerald"
          loading={chartLoading}
        />
        <KpiCard
          title="Utilità Canali Digitali"
          value={fmt(kpi.avgDigitale)}
          badge="media /10"
          color="amber"
          loading={chartLoading}
        />
        <KpiCard
          title="Utilità Webinar"
          value={fmt(kpi.avgWebinar)}
          badge="media /10"
          color="rose"
          loading={chartLoading}
        />
      </div>

      {/* Chart */}
      <ChannelBarChart
        data={chartData}
        title="Utilità percepita per canale (scala 1–10)"
        loading={chartLoading}
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
