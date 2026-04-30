import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Variabili Supabase mancanti. Crea frontend/.env.local con VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY'
  )
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export function avg(rows, key) {
  const vals = rows.map(r => r[key]).filter(v => v != null && !isNaN(Number(v)))
  return vals.length > 0 ? vals.reduce((a, b) => a + Number(b), 0) / vals.length : null
}

export function fmt(val, decimals = 1) {
  return val != null ? Number(val).toFixed(decimals) : '—'
}

export function distinct(rows, key) {
  return [...new Set(rows.map(r => r[key]))].filter(Boolean).sort()
}
