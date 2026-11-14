// UI strings in English and Turkish (owner: C).
// The app is shown in Turkish during development; before the final submission
// set LANG = "en" (the challenge requires English). Text that comes from the
// backend (catalog names, descriptions, glossary, interpretation) is not
// translated here.

// Arayüz dili: geliştirme sırasında "tr"; projeyi teslim etmeden önce "en" yapılacak.
export const LANG: "en" | "tr" = "tr"

const TEXTS = {
  // --- Page ---------------------------------------------------------------
  appTitle: { en: "Earth Trend Detective", tr: "Dünya Trend Dedektifi" },
  tagline: {
    en: "Become a data detective: find out what's changing on Earth, where, how fast, and whether it's significant.",
    tr: "Veri dedektifi ol: Dünya'da neyin, nerede, ne hızla değiştiğini ve bunun anlamlı olup olmadığını keşfet.",
  },
  stubWarningTitle: { en: "Development build", tr: "Geliştirme sürümü" },
  stubWarning: {
    en: "Using placeholder modules for {modules}. Numbers are mock data.",
    tr: "{modules} için geçici modüller kullanılıyor. Sayılar sahte veridir.",
  },
  tabDetective: { en: "Detective Mode", tr: "Dedektif Modu" },
  tabExplore: { en: "Explore", tr: "Keşfet" },
  tabCases: { en: "Case Files", tr: "Vaka Dosyaları" },
  tabCompare: { en: "Compare", tr: "Karşılaştır" },
  comingSoon: {
    en: "{what} is coming soon. Use {explore} for now.",
    tr: "{what} yakında geliyor. Şimdilik {explore} sekmesini kullan.",
  },
  footer: {
    en: "Datasets: {datasets}. Data: NASA Giovanni, pre-downloaded on {date}",
    tr: "Veri setleri: {datasets}. Veri: NASA Giovanni, önceden indirildi: {date}",
  },
  loadError: {
    en: "Could not reach the backend. Is `uvicorn api:app` running?",
    tr: "Backend'e ulaşılamadı. `uvicorn api:app` çalışıyor mu?",
  },
  // --- Explore ------------------------------------------------------------
  region: { en: "Region", tr: "Bölge" },
  variable: { en: "Variable", tr: "Değişken" },
  noData: { en: "No data available yet for {variable} in {region}.", tr: "{region} için {variable} verisi henüz yok." },
  notEnoughData: { en: "Not enough data to analyse this series.", tr: "Bu seriyi analiz etmek için yeterli veri yok." },
  sourceCaption: {
    en: "Source dataset: {dataset} · {unit} · area-averaged over the {region}",
    tr: "Kaynak veri seti: {dataset} · {unit} · {region} genelinde alan ortalaması",
  },
  // --- Result card --------------------------------------------------------
  changePerDecade: { en: "Change per decade", tr: "10 yıldaki değişim" },
  pctPerDecade: { en: "% per decade", tr: "10 yılda % değişim" },
  pctHelp: {
    en: "Change per decade relative to the long-term average.",
    tr: "10 yıllık değişimin uzun dönem ortalamaya oranı.",
  },
  significance: { en: "Significance", tr: "Anlamlılık" },
  significant: { en: "Significant", tr: "Anlamlı" },
  notSignificant: { en: "Not significant", tr: "Anlamlı değil" },
  notAvailable: { en: "n/a", tr: "yok" },
  statsDetails: { en: "Statistical details", tr: "İstatistik detayları" },
  olsSlope: { en: "OLS slope", tr: "OLS eğimi" },
  ciRange: { en: "95% CI: {low} to {high}", tr: "%95 GA: {low} ile {high} arası" },
  mkP: { en: "Mann-Kendall p-value", tr: "Mann-Kendall p-değeri" },
  senSlope: { en: "Sen's slope", tr: "Sen eğimi" },
  yearsOfData: { en: "Years of data", tr: "Veri yılı" },
  perDecadeUnit: { en: "{unit}/decade", tr: "{unit}/10 yıl" },
  anomalyNote: {
    en: "The trend is fitted to monthly anomalies (each month minus its long-term average for that calendar month), so the seasonal cycle does not create a fake trend.",
    tr: "Trend, aylık anomaliler üzerinden hesaplanır (her ay eksi o takvim ayının uzun dönem ortalaması); böylece mevsimsel döngü sahte bir trend oluşturmaz.",
  },
  // --- Chart --------------------------------------------------------------
  increasing: { en: "increasing", tr: "artıyor" },
  decreasing: { en: "decreasing", tr: "azalıyor" },
  sigShort: { en: "significant", tr: "anlamlı" },
  notSigShort: { en: "not significant", tr: "anlamlı değil" },
  monthlyValues: { en: "Monthly values", tr: "Aylık değerler" },
  anomaliesAndTrend: { en: "Anomalies and trend: {label}", tr: "Anomaliler ve trend: {label}" },
  monthlyValue: { en: "Monthly value", tr: "Aylık değer" },
  movingAvg: { en: "12-month moving average", tr: "12 aylık hareketli ortalama" },
  anomaly: { en: "Anomaly", tr: "Anomali" },
  ciBand: { en: "95% confidence band", tr: "%95 güven bandı" },
  trend: { en: "Trend", tr: "Trend" },
} as const

export type TextKey = keyof typeof TEXTS

// Seçili dildeki metni anahtarına göre döndürür; {…} yer tutucularını doldurur.
// Örnek: t("noData", { variable: "Yağış", region: "Konya" })
export function t(key: TextKey, vars?: Record<string, string | number>): string {
  let text: string = TEXTS[key][LANG]
  for (const [name, value] of Object.entries(vars ?? {})) {
    text = text.replaceAll(`{${name}}`, String(value))
  }
  return text
}

// Sayıyı seçili dile göre biçimlendirir (Türkçede ondalık ayırıcı virgüldür).
// sign=true ise pozitif sayıların başına + konur.
export function fmt(value: number, digits = 2, sign = false): string {
  const s = value.toLocaleString(LANG === "tr" ? "tr-TR" : "en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
  return sign && value > 0 ? `+${s}` : s
}
