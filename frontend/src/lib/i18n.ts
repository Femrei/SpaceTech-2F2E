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
    en: "Development build: placeholder modules for {modules}.",
    tr: "Geliştirme sürümü: {modules} için geçici modüller kullanılıyor.",
  },
  mockDataWarning: {
    en: "The numbers are synthetic test data, not real NASA measurements.",
    tr: "Sayılar sahte test verisidir, gerçek NASA ölçümleri değildir.",
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
    en: "Couldn't load the data. Check your connection and try again.",
    tr: "Veriler yüklenemedi. Bağlantını kontrol edip tekrar dene.",
  },
  retry: { en: "Try again", tr: "Tekrar dene" },
  toLight: { en: "Switch to light theme", tr: "Açık temaya geç" },
  toDark: { en: "Switch to dark theme", tr: "Koyu temaya geç" },
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
  kpiChangeCaption: { en: "average rate (Sen's slope)", tr: "ortalama hız (Sen eğimi)" },
  kpiPercent: { en: "Change in %", tr: "Yüzde değişim" },
  kpiPercentCaption: { en: "per 10 years, vs. long-term average", tr: "10 yılda, uzun dönem ortalamaya göre" },
  noPercentCaption: {
    en: "not meaningful for this measurement (its zero point is arbitrary, e.g. 0 °C)",
    tr: "bu ölçüm için anlamlı değil (sıfır noktası keyfi, ör. 0 °C)",
  },
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
  showMonthly: { en: "Show monthly values", tr: "Aylık değerleri göster" },
  anomaly: { en: "Difference from normal", tr: "Normalden fark" },
  anomalyYearly: { en: "Yearly difference from normal", tr: "Yıllık normalden fark" },
  year: { en: "Year", tr: "Yıl" },
  sourceCaption: {
    en: "Source: {dataset} · monthly, averaged over the whole region",
    tr: "Kaynak: {dataset} · aylık, bölgenin tamamının ortalaması",
  },
  // Explanation card
  whatItMeans: { en: "What does this mean?", tr: "Bu ne demek?" },
  howToRead: { en: "How to read the chart", tr: "Grafik nasıl okunur?" },
  readSimple1: {
    en: "Tick \"Show monthly values\" to add each month's raw value as a thin grey line; it goes up and down with the seasons.",
    tr: "\"Aylık değerleri göster\" kutucuğuyla her ayın ham değerini ince gri çizgi olarak ekleyebilirsin; mevsimlere göre iner çıkar.",
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
    en: "Each bar is one year: how far that year's months were, on average, from their normal (e.g. each July vs. an average July).",
    tr: "Her çubuk bir yıl: o yılın aylarının kendi normallerinden ortalama ne kadar saptığını gösterir (ör. her Temmuz, ortalama bir Temmuz'a göre).",
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
  // --- Map ----------------------------------------------------------------
  mapTitle: { en: "Regions on the map", tr: "Bölgeler haritada" },
  mapHint: { en: "Click a region to select it.", tr: "Seçmek için bir bölgeye tıkla." },
  // --- Compare ------------------------------------------------------------
  compareIntro: {
    en: "Same measurement, two regions: are they changing the same way?",
    tr: "Aynı ölçüm, iki bölge: ikisi de aynı yönde mi değişiyor?",
  },
  regionA: { en: "Region 1", tr: "1. bölge" },
  regionB: { en: "Region 2", tr: "2. bölge" },
  sameRegion: { en: "Pick two different regions.", tr: "İki farklı bölge seç." },
  compareChartTitle: { en: "Difference from normal (12-month average)", tr: "Normalden fark (12 aylık ortalama)" },
  compareChartTitlePct: {
    en: "Difference from normal, % of each region's average (12-month average)",
    tr: "Normalden fark, bölgenin kendi ortalamasına göre % (12 aylık ortalama)",
  },
  compareChartDesc: {
    en: "Each solid line shows how far that region is from its own normal; dashed lines are the long-term trends.",
    tr: "Her düz çizgi o bölgenin kendi normalinden ne kadar saptığını gösterir; kesikli çizgiler uzun dönem eğilimlerdir.",
  },
  oppositeBadge: { en: "Opposite directions!", tr: "Zıt yönler!" },
  sameBadge: { en: "Same direction", tr: "Aynı yön" },
  compareWhy: { en: "Why does this matter?", tr: "Bu neden önemli?" },
  compareWhyText: {
    en: "The same climate process can push different places in opposite directions: one region dries while another gets wetter. One region's story is not the whole country's.",
    tr: "Aynı iklim süreci farklı yerleri zıt yönlere itebilir: bir bölge kururken diğeri nemlenebilir. Tek bir bölgenin hikâyesi bütün ülkenin hikâyesi değildir.",
  },
  // --- Detective Mode -----------------------------------------------------
  detIntro: {
    en: "Work like a detective: pick a question, follow the clues, and let the data decide.",
    tr: "Bir dedektif gibi çalış: bir soru seç, ipuçlarını takip et, kararı veriye bırak.",
  },
  detStep1: { en: "Pick a question", tr: "Bir soru seç" },
  detStep2: { en: "Where to start?", tr: "Nereden başlayalım?" },
  detStep3: { en: "Investigate", tr: "İncele" },
  investigate: { en: "Investigate", tr: "İncele" },
  bestPick: { en: "Best place to start", tr: "En iyi başlangıç" },
  followClue: { en: "Follow the clue", tr: "İpucunu takip et" },
  openCompare: { en: "Compare regions", tr: "Bölgeleri karşılaştır" },
  startOver: { en: "Start over", tr: "Baştan başla" },
  backToSuggestions: { en: "Back to suggestions", tr: "Önerilere dön" },
  clueTitle: { en: "Detective's note", tr: "Dedektifin notu" },
  trail: { en: "Your trail", tr: "İzlediğin yol" },
  alreadyVisited: {
    en: "You already checked {done}. Next suspect: {next}.",
    tr: "{done} zaten incelendi. Sıradaki şüpheli: {next}.",
  },
  allVisited: {
    en: "You've checked every measurement here. Compare with another region next.",
    tr: "Bu bölgedeki tüm ölçümlere baktın. Sırada başka bir bölgeyle karşılaştırmak var.",
  },
  // --- Case Files ---------------------------------------------------------
  casesIntro: {
    en: "Open a ready-made case and solve it like a detective.",
    tr: "Hazır bir vakayı aç ve bir dedektif gibi çöz.",
  },
  openCase: { en: "Open case", tr: "Vakayı aç" },
  backToCases: { en: "Back to cases", tr: "Vakalara dön" },
  compareCase: { en: "Two regions", tr: "İki bölge" },
  mockCases: {
    en: "Case stories are placeholders until the real results are in.",
    tr: "Vaka metinleri geçici; gerçek sonuçlar gelince yeniden yazılacak.",
  },
  // --- About sheet --------------------------------------------------------
  about: { en: "About", tr: "Hakkında" },
  aboutTitle: { en: "About this app", tr: "Bu uygulama hakkında" },
  aboutText: {
    en: "Earth Trend Detective lets anyone check what NASA satellite and model data say about how rain, soil moisture and temperature have changed in three regions of Türkiye since 2001, and whether those changes are statistically significant.",
    tr: "Dünya Trend Dedektifi, NASA uydu ve model verilerinin Türkiye'deki üç bölgede 2001'den bu yana yağış, toprak nemi ve sıcaklık hakkında ne söylediğini ve bu değişimlerin istatistiksel olarak anlamlı olup olmadığını herkesin kontrol edebilmesini sağlar.",
  },
  howItWorks: { en: "How it works", tr: "Nasıl çalışır?" },
  how1: {
    en: "Monthly, area-averaged values are downloaded from NASA Giovanni for 2001–2025.",
    tr: "2001–2025 arası aylık, bölge ortalaması değerler NASA Giovanni'den indirilir.",
  },
  how2: {
    en: "The seasonal cycle is removed: each month is compared with the normal for that calendar month (anomaly).",
    tr: "Mevsim etkisi çıkarılır: her ay, aynı takvim ayının normaliyle karşılaştırılır (anomali).",
  },
  how3: {
    en: "A straight-line trend (OLS) gives the rate per decade and its 95% range.",
    tr: "Doğrusal bir eğilim (OLS) 10 yıllık değişim hızını ve %95 aralığını verir.",
  },
  how4: {
    en: "The Mann-Kendall test checks whether the trend could just be chance (significant if p < 0.05).",
    tr: "Mann-Kendall testi eğilimin tesadüf olup olamayacağını kontrol eder (p < 0,05 ise anlamlı).",
  },
  dataSources: { en: "Data sources", tr: "Veri kaynakları" },
  sourcePrecip: {
    en: "Precipitation: GPM IMERG monthly (GPM_3IMERGM), NASA Global Precipitation Measurement mission.",
    tr: "Yağış: GPM IMERG aylık (GPM_3IMERGM), NASA Küresel Yağış Ölçüm (GPM) görevi.",
  },
  sourceSoil: {
    en: "Soil moisture (0–10 cm): GLDAS Noah 0.25° monthly (GLDAS_NOAH025_M), NASA land surface model.",
    tr: "Toprak nemi (0–10 cm): GLDAS Noah 0,25° aylık (GLDAS_NOAH025_M), NASA kara yüzeyi modeli.",
  },
  sourceTemp: {
    en: "Air temperature (2 m): MERRA-2 monthly (M2TMNXSLV), NASA atmospheric reanalysis.",
    tr: "Hava sıcaklığı (2 m): MERRA-2 aylık (M2TMNXSLV), NASA atmosfer yeniden analizi.",
  },
  sourceAccess: {
    en: "All data accessed through NASA Giovanni (giovanni.gsfc.nasa.gov), downloaded on {date}.",
    tr: "Tüm veriler NASA Giovanni (giovanni.gsfc.nasa.gov) üzerinden alındı; indirme tarihi: {date}.",
  },
  limitsTitle: { en: "Keep in mind", tr: "Akılda tut" },
  limitsText: {
    en: "25 years is a short record for climate. A trend tells you what changed, not why. Regional averages hide local differences.",
    tr: "25 yıl iklim için kısa bir süre. Eğilim neyin değiştiğini söyler, nedenini değil. Bölge ortalamaları yerel farkları gizler.",
  },
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

// p-değerini yazar: çok küçükse "p < 0,001" (0,000 gibi yanıltıcı bir sıfır yerine).
export function fmtP(p: number): string {
  return p < 0.001 ? `p < ${fmt(0.001, 3)}` : `p = ${fmt(p, 3)}`
}
