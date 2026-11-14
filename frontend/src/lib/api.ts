// Types and fetch helpers for the FastAPI backend (api.py).

// D'nin catalog.json şeması (data/catalog.json). Sadece arayüzün kullandığı alanlar.
export interface Variable {
  id: string
  name: string
  unit: string
  dataset: string
  source?: string
  period: { start: string; end: string }
  period_note?: string | null
  short_description: string
  long_description: string
  themes: string[]
}

export interface Region {
  id: string
  name: string
  name_in_text?: string
  bbox: { west: number; south: number; east: number; north: number }
  lat: number
  lon: number
  description: string
  teaser?: string
  themes?: string[]
  compare_with?: string
}

export interface Case {
  id: string
  title: string
  story: string
  region_id: string
  variable_id: string
  compare_region_id: string | null
  // Çok adımlı vaka: aynı bölgede sırayla incelenecek değişkenler (ilki variable_id).
  chain?: string[] | null
}

// D'nin ipucu kural tablosu; "*" her değerle eşleşir.
export interface HintRule {
  variable_id: string
  direction: string
  significant: boolean | "*"
  text: string
  next: { variable_id: string; region_id: string } | null
}

export interface Meta {
  variables: Variable[]
  regions: Region[]
  glossary: Record<string, string>
  cases: Case[]
  themes: Record<string, string>
  pairs: [string, string][]
  data_downloaded_on: string
  hints: HintRule[]
  mock_data: boolean
  no_percent_variables: string[]
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

// B'nin analyze_trend() sonucunun tek değerli alanları (src/trend.py RESULT_KEYS).
// Yön, anlamlılık ve yüzde değişim Sen eğiminden / mevsimsel Mann-Kendall testinden gelir;
// slope_per_decade ve ci_low/ci_high doğrusal (OLS) eğimdir.
export interface TrendResult {
  n: number
  start: string
  end: string
  mk_tau?: number
  method?: string
  slope_per_decade: number
  ci_low: number
  ci_high: number
  ols_p: number
  mk_p: number
  sen_slope_per_decade: number
  significant: boolean
  direction: "increasing" | "decreasing" | "no change"
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
  // D'nin next_step(): ipucu metni + takip edilecek değişken/bölge (yoksa null).
  next_step: { text: string; variable_id: string | null; region_id: string | null }
}

export interface ComparePoint {
  date: string
  a: number | null
  b: number | null
  trend_a: number | null
  trend_b: number | null
}

export interface Comparison {
  points: ComparePoint[]
  result_a: TrendResult
  result_b: TrendResult
  comparison: { same_direction: boolean; both_significant: boolean; summary: string }
}

export interface Suggestion {
  region_id: string
  variable_id: string
  reason: string
}

export interface OverviewItem {
  region_id: string
  variable_id: string
  error?: string
  slope_per_decade?: number
  sen_slope_per_decade?: number
  percent_change_per_decade?: number | null
  significant?: boolean
  direction?: "increasing" | "decreasing" | "no change"
  mk_p?: number
  yearly?: { year: number; value: number | null }[]
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

// Karşılaştır sekmesi: aynı değişken için iki bölgenin verisini ve karşılaştırma özetini getirir.
export function fetchCompare(variable: string, regionA: string, regionB: string): Promise<Comparison> {
  const q = new URLSearchParams({ variable, region_a: regionA, region_b: regionB })
  return getJson<Comparison>(`/api/compare?${q}`)
}

// Dedektif Modu: seçilen temaya uygun bölge + değişken önerilerini getirir.
export function fetchSuggestions(theme: string): Promise<Suggestion[]> {
  return getJson<Suggestion[]>(`/api/suggest?${new URLSearchParams({ theme })}`)
}

// Genel bakış ızgarası için tüm bölge + değişken çiftlerinin trend özetini getirir.
export function fetchOverview(): Promise<OverviewItem[]> {
  return getJson<OverviewItem[]>("/api/overview")
}

// Seçilen bölge + değişken için grafik noktalarını ve trend sonucunu getirir.
export function fetchAnalysis(region: string, variable: string): Promise<Analysis> {
  const q = new URLSearchParams({ region, variable })
  return getJson<Analysis>(`/api/analysis?${q}`)
}
