// Types and fetch helpers for the FastAPI backend (api.py).

export interface Variable {
  id: string
  name: string
  unit: string
  dataset: string
  period: string
  short_description: string
  long_description: string
  themes: string[]
}

export interface Region {
  id: string
  name: string
  bbox: [number, number, number, number]
  lat: number
  lon: number
  description: string
}

export interface Case {
  id: string
  title: string
  story: string
  region_id: string
  variable_id: string
  compare_region_id: string | null
}

export interface Meta {
  variables: Variable[]
  regions: Region[]
  glossary: Record<string, string>
  cases: Case[]
  themes: Record<string, string>
  pairs: [string, string][]
  data_downloaded_on: string
  stubs_in_use: string[]
}

export interface Point {
  date: string
  value: number | null
  smooth: number | null
  anomaly: number | null
  trend: number | null
  ci_low: number | null
  ci_high: number | null
}

export interface TrendResult {
  slope_per_decade: number
  ci_low: number
  ci_high: number
  ols_p: number
  mk_p: number
  sen_slope_per_decade: number
  significant: boolean
  direction: "increasing" | "decreasing"
  percent_change_per_decade: number | null
  mean_value: number
  n_years: number
  start_year: number
  end_year: number
  years_needed_estimate: number | null
}

export interface Analysis {
  points: Point[]
  result: TrendResult
  interpretation: string
  next_step_hint: string
}

// Backend'den hata dönerse (404, 422 …) mesajı ve durum kodunu taşıyan hata tipi.
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// Verilen adrese GET isteği atar, JSON cevabı döndürür; hata varsa ApiError fırlatır.
async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

// Açılışta bir kez çağrılır: katalog, sözlük, temalar, veri çiftleri vb.
export function fetchMeta(): Promise<Meta> {
  return getJson<Meta>("/api/meta")
}

// Seçilen bölge + değişken için grafik noktalarını ve trend sonucunu getirir.
export function fetchAnalysis(region: string, variable: string): Promise<Analysis> {
  const q = new URLSearchParams({ region, variable })
  return getJson<Analysis>(`/api/analysis?${q}`)
}
