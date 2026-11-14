// UI strings in English and Turkish (owner: C).
// The app is shown in Turkish during development; before the final submission
// set LANG = "en" (the challenge requires English). Turkish versions of the
// content that comes from the backend (names, descriptions, glossary,
// interpretation) live in content.ts.

// Arayüz dili: geliştirme sırasında "tr"; projeyi teslim etmeden önce "en" yapılacak.
export const LANG: "en" | "tr" = "tr"

const TEXTS = {
  // --- Page ---------------------------------------------------------------
  appTitle: { en: "Earth Trend Detective", tr: "Dünya Trend Dedektifi" },
  appSubtitle: {
    en: "What is changing on Earth, where, how fast, and is it real?",
    tr: "Dünya'da ne, nerede, ne hızla değişiyor ve bu değişim gerçek mi?",
  },
  stubWarning: {
    en: "Development build: placeholder modules for {modules}. Numbers are mock data.",
    tr: "Geliştirme sürümü: {modules} için geçici modüller kullanılıyor. Sayılar sahte veridir.",
  },
  tabDetective: { en: "Detective Mode", tr: "Dedektif Modu" },
  tabExplore: { en: "Dashboard", tr: "Pano" },
  tabCases: { en: "Case Files", tr: "Vaka Dosyaları" },
  tabCompare: { en: "Compare", tr: "Karşılaştır" },
  comingSoon: {
    en: "{what} is coming soon. Use the {explore} tab for now.",
    tr: "{what} yakında geliyor. Şimdilik {explore} sekmesini kullan.",
  },
  footer: {
    en: "Data: NASA Giovanni ({datasets}), pre-downloaded on {date}.",
    tr: "Veri: NASA Giovanni ({datasets}), önceden indirildi: {date}.",
  },
  loadError: {
    en: "Could not reach the backend. Is `uvicorn api:app` running?",
    tr: "Sunucuya ulaşılamadı. `uvicorn api:app` çalışıyor mu?",
  },
  // --- Dashboard ----------------------------------------------------------
  intro: {
    en: "Pick a region and a measurement to see what changed over the last 25 years, and whether the change is real or just chance.",
    tr: "Bir bölge ve bir ölçüm seç; son 25 yılda ne değiştiğini ve bu değişimin gerçek mi yoksa tesadüf mü olduğunu gör.",
  },
  region: { en: "Region", tr: "Bölge" },
  variable: { en: "Measurement", tr: "Ölçüm" },
  noData: { en: "No data available yet for {variable} in {region}.", tr: "{region} için {variable} verisi henüz yok." },
  notEnoughData: { en: "Not enough data to analyse this series.", tr: "Bu seriyi analiz etmek için yeterli veri yok." },
  // KPI tiles
  kpiDirection: { en: "Overall direction", tr: "Genel gidişat" },
  kpiDirectionHelp: {
    en: "Is the long-term trend going up or down, and is it clear enough to count?",
    tr: "Uzun dönemli eğilim yukarı mı aşağı mı, ve bunu söyleyecek kadar net mi?",
  },
  up: { en: "Increasing", tr: "Artıyor" },
  down: { en: "Decreasing", tr: "Azalıyor" },
  flat: { en: "No clear change", tr: "Belirgin değişim yok" },
  kpiChange: { en: "Change per 10 years", tr: "10 yıldaki değişim" },
  kpiChangeCaption: { en: "average rate", tr: "ortalama hız" },
  kpiPercent: { en: "Change in %", tr: "Yüzde değişim" },
  kpiPercentCaption: { en: "per 10 years, vs. long-term average", tr: "10 yılda, uzun dönem ortalamaya göre" },
  kpiReliability: { en: "Is it real?", tr: "Gerçek mi?" },
  significant: { en: "Yes, significant", tr: "Evet, anlamlı" },
  notSignificant: { en: "Not yet", tr: "Henüz değil" },
  sigCaption: { en: "very unlikely to be chance", tr: "tesadüf olma ihtimali çok düşük" },
  notSigCaption: { en: "can't be told apart from natural ups and downs", tr: "doğal iniş çıkışlardan ayırt edilemiyor" },
  notAvailable: { en: "n/a", tr: "yok" },
  // Chart card
  viewSimple: { en: "Simple", tr: "Basit" },
  viewDetailed: { en: "Detailed", tr: "Detaylı" },
  monthlyValue: { en: "Monthly value", tr: "Aylık değer" },
  movingAvg: { en: "12-month average", tr: "12 aylık ortalama" },
  trendLine: { en: "Long-term trend", tr: "Uzun dönem eğilim" },
  ciBand: { en: "Uncertainty range (95%)", tr: "Belirsizlik aralığı (%95)" },
  anomaly: { en: "Difference from normal", tr: "Normalden fark" },
  year: { en: "Year", tr: "Yıl" },
  sourceCaption: {
    en: "Source: {dataset} · monthly, averaged over the whole region",
    tr: "Kaynak: {dataset} · aylık, bölgenin tamamının ortalaması",
  },
  // Explanation card
  whatItMeans: { en: "What does this mean?", tr: "Bu ne demek?" },
  howToRead: { en: "How to read the chart", tr: "Grafik nasıl okunur?" },
  readSimple1: {
    en: "The thin grey line is each month's value; it goes up and down with the seasons.",
    tr: "İnce gri çizgi her ayın değeri; mevsimlere göre iner çıkar.",
  },
  readSimple2: {
    en: "The thick line is the 12-month average: the seasons are smoothed out.",
    tr: "Kalın çizgi 12 aylık ortalama: mevsim etkisi düzleştirilmiştir.",
  },
  readSimple3: {
    en: "The dashed coloured line is the long-term trend; the shaded area shows its uncertainty.",
    tr: "Kesikli renkli çizgi uzun dönem eğilim; etrafındaki gölge belirsizlik aralığıdır.",
  },
  readDetailed1: {
    en: "Each bar shows how much a month differed from a normal month of the same kind (e.g. this July vs. an average July).",
    tr: "Her çubuk, o ayın aynı takvim ayının normalinden ne kadar saptığını gösterir (ör. bu Temmuz, ortalama bir Temmuz'a göre).",
  },
  readDetailed2: {
    en: "Bars above zero: higher than normal. Below zero: lower than normal.",
    tr: "Sıfırın üstündeki çubuklar normalden yüksek, altındakiler normalden düşük.",
  },
  readColors: {
    en: "Colours: orange = increasing, blue = decreasing, grey = no clear change.",
    tr: "Renkler: turuncu = artıyor, mavi = azalıyor, gri = belirgin değişim yok.",
  },
  statsDetails: { en: "Statistical details", tr: "İstatistik detayları" },
  olsSlope: { en: "Linear trend (OLS)", tr: "Doğrusal eğim (OLS)" },
  ciRange: { en: "95% range: {low} to {high}", tr: "%95 aralık: {low} ile {high} arası" },
  mkP: { en: "p-value (Mann-Kendall)", tr: "p-değeri (Mann-Kendall)" },
  senSlope: { en: "Sen's slope", tr: "Sen eğimi" },
  yearsOfData: { en: "Years of data", tr: "Veri yılı" },
  perDecadeUnit: { en: "{unit} / 10 yr", tr: "{unit} / 10 yıl" },
  // Overview grid
  overviewTitle: { en: "All regions at a glance", tr: "Tüm bölgeler bir bakışta" },
  overviewHint: {
    en: "Click a box to open it in the dashboard above.",
    tr: "Bir kutuya tıklayınca ayrıntısı yukarıda açılır.",
  },
  selected: { en: "selected", tr: "seçili" },
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
  const s = Math.abs(value).toLocaleString(LANG === "tr" ? "tr-TR" : "en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
  if (value < 0) return `−${s}`
  return sign && value > 0 ? `+${s}` : s
}

// Yüzdeyi dile göre yazar: Türkçede işaret başta ("−%8,0"), İngilizcede sonda ("−8.0%").
export function fmtPct(value: number, digits = 1): string {
  const body = fmt(Math.abs(value), digits)
  const sign = value < 0 ? "−" : value > 0 ? "+" : ""
  return LANG === "tr" ? `${sign}%${body}` : `${sign}${body}%`
}
