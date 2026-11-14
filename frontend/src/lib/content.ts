// Display content for regions, variables and glossary terms, plus the
// plain-language explanation of a trend result (owner: C).
//
// The backend (D's catalog, B's interpret()) provides English content. While
// LANG is "tr" we show the Turkish versions below instead, keyed by id, so the
// teammates' files never need to change. Unknown ids fall back to the backend.

import type { HintRule, Region, TrendResult, Variable } from "@/lib/api"
import { LANG, fmt } from "@/lib/i18n"

// Turkish versions of D's catalog texts (data/catalog.json), keyed by id.
const REGIONS_TR: Record<string, { name: string; description: string; teaser: string }> = {
  konya: {
    name: "Konya Kapalı Havzası",
    description:
      "İç Anadolu'da, nehirleri denize ulaşmayan yarı kurak bir plato: su havzanın içinde toplanır ya da buharlaşır. " +
      "Ovanın kendisi yılda yalnızca 300 mm civarında yağış alır (çevredeki tepeleri de kapsayan kutumuzun ortalaması yaklaşık 440 mm), " +
      "yine de sık sık Türkiye'nin tahıl ambarı diye anılır ve tarımı sulama için büyük ölçüde yeraltı suyuna dayanır. " +
      "Düşen yeraltı suyu seviyeleri, ovada açılan obrukların artmasıyla ilişkilendiriliyor.",
    teaser: "Konya Türkiye'nin tahıl ambarı ve tarlaları kıt suya bağlı.",
  },
  van: {
    name: "Van Gölü Havzası",
    description:
      "Doğu Anadolu'da, ülkenin en büyük gölü Van Gölü çevresindeki yüksek bir plato; göl yüzeyi deniz seviyesinden yaklaşık 1.640 m yukarıda. " +
      "Gölün çıkışı olmadığı için suyu tuzlu ve alkalidir (sodalı göl). Kışlar uzun, soğuk ve karlıdır (kutumuzda ocak ortalaması yaklaşık −7 °C), " +
      "bu yüzden sıcaklıktaki değişimler kar örtüsünü, bahar erimesini ve göle ulaşan suyu etkiler. " +
      "Kutumuz gölün kendisini de kapsadığı için bölge ortalamaları gölle karayı karıştırır.",
    teaser: "Van'ın yüksek ve soğuk platosu sıcaklıktaki ve kardaki değişimlere duyarlı.",
  },
  black_sea: {
    name: "Doğu Karadeniz",
    description:
      "Trabzon ve Rize çevresinde, Karadeniz kıyısı ile Kaçkar Dağları'nın sırtı arasındaki dik ve yeşil yamaçlar; çay bahçeleriyle ünlü. " +
      "Denizden gelen nemli hava dağlara tırmanmak zorunda kalır ve burayı ülkenin en yağışlı yeri yapar: Rize yakınlarındaki kıyı yılda 2.000 mm'den fazla yağış alır, " +
      "kutumuzun ortalaması yaklaşık 1.100 mm. Kutunun çoğu dağlık olduğu için serindir: ortalama yaklaşık 7,5 °C, temmuzda bile 18 °C'nin altında. " +
      "Buradaki şiddetli yağışlar sel ve heyelanlara yol açabilir.",
    teaser: "Doğu Karadeniz'in yağmurlu dağları Türkiye'nin en ıslak köşesi; kuru iç bölgelerle iyi bir karşıtlık.",
  },
}

const VARIABLES_TR: Record<string, { name: string; unit: string; short: string; periodNote?: string }> = {
  precip: {
    name: "Yağış",
    unit: "mm/ay",
    short: "Her ay ne kadar yağmur ve kar yağdığı; düz bir zeminde bırakacağı su derinliği olarak ölçülür.",
    periodNote:
      "IMERG Final Run aylık verisi indirme sırasında yalnızca Eylül 2025'e kadar mevcuttu; Ekim–Aralık 2025 eksik.",
  },
  soil_moisture: {
    name: "Toprak nemi",
    unit: "kg/m²",
    short: "Toprağın üst 10 cm'sinin ne kadar ıslak olduğu: bitkilerin kolayca ulaşabildiği su gibi düşünebilirsin.",
  },
  temp: {
    name: "Hava sıcaklığı",
    unit: "°C",
    short: "Yerden yaklaşık 2 metre yükseklikteki havanın sıcaklığı: insanların ve ekinlerin hissettiği yükseklik.",
  },
  // DENEME: "Konumunu seç" sekmesindeki NASA POWER ölçümleri.
  power_temp: {
    name: "Hava sıcaklığı",
    unit: "°C",
    short: "Yerden yaklaşık 2 metre yükseklikteki havanın sıcaklığı.",
  },
  power_precip: {
    name: "Yağış",
    unit: "mm/ay",
    short: "Her ay düşen yağmur ve kar (MERRA-2, ölçümlerle düzeltilmiş).",
  },
  power_soil_wetness: {
    name: "Yüzey toprak ıslaklığı",
    // "puan": değerin kendisi yüzde olduğu için değişim "yüzde puan"dır; yanındaki
    // göreli değişimle (%1,6 gibi) karışmasın.
    unit: "yüzde puan",
    short: "Toprağın üst katmanının doygunluğa ne kadar yakın olduğu: %0 kupkuru, %100 tamamen doygun.",
    periodNote: "NASA POWER bu değeri %1'lik adımlarla verir; çok yavaş değişimlerde eğim 0 görünebilir.",
  },
}

const GLOSSARY_TR: Record<string, string> = {
  "trend":
    "Bir büyüklüğün yıllar içindeki uzun dönemli yönü; mevsimlerin ve tek tek yılların iniş çıkışları bir kenara bırakıldığında kalan.",
  "anomaly":
    "Bir ayın, o takvim ayı için normal olandan ne kadar farklı olduğu. +1,5 °C'lik bir Temmuz anomalisi, o Temmuz'un ortalama bir Temmuz'dan 1,5 °C daha sıcak olduğu demektir.",
  "seasonal cycle":
    "Her yıl tekrarlanan düzenli yükseliş ve düşüş, sıcak yazlar ve soğuk kışlar gibi. Uzun dönemli bir eğilimi gizlemesin ya da sahte bir eğilim üretmesin diye onu çıkarıyoruz.",
  "climatology":
    "Her takvim ayının uzun dönem ortalaması, örneğin bütün Ocakların ortalaması. Anomaliler buna göre ölçülür.",
  "p-value":
    "Gerçekte hiçbir şey değişmiyorken, en az bu kadar güçlü bir eğilimin sırf şans eseri ortaya çıkma ihtimali. 0,05'in altı = anlamlı.",
  "statistically significant":
    "Eğilim, doğal iniş çıkışlara kıyasla tesadüf olamayacak kadar güçlü (burada: p < 0,05). Değişimin ne kadar büyük ya da önemli olduğunu ya da neyin yol açtığını söylemez.",
  "mann-kendall test":
    "Değerleri ikişer ikişer karşılaştırarak zamanla artma ya da azalma eğiliminde olup olmadıklarını kontrol eden test. Mevsimsel sürümünü kullanıyoruz: yalnızca farklı yılların aynı aylarını karşılaştırır (Ocak ile Ocak), böylece mevsim döngüsü onu yanıltamaz.",
  "sen's slope":
    "Bir büyüklüğün ne hızla değiştiğine dair sağlam bir tahmin: nokta çiftleri arasındaki eğimlerin ortancası. Birkaç aşırı ay onu neredeyse hiç etkilemez.",
  "linear regression (ols)":
    "Anomalileri en iyi izleyen düz çizgiyi bulmak (en küçük kareler yöntemi). Bu çizginin eğimi, grafikte çizilen eğilim çizgisidir.",
  "confidence interval":
    "Verideki gürültü göz önüne alındığında, gerçek değişim hızı için makul değerlerin aralığı. %95'lik aralık sıfırı içermiyorsa, \"hiç değişim yok\" fikri veriyle zor bağdaşır.",
  "per decade":
    "Hızlar 10 yıl başına verilir. 10 yılda −1,2 kg/m², her 10 yılda yaklaşık 1,2 kg/m², 25 yılda yaklaşık 3 kg/m² düşüş demektir.",
  "area-averaged":
    "Bölgenin tamamı için tek bir değer: bölge kutusundaki bütün ızgara hücrelerinin ortalaması. Bölgenin içindeki yerler ortalamadan farklı davranabilir.",
}

// Bölgenin ekranda gösterilecek adı (Türkçe modda çeviri, yoksa backend'deki ad).
export function regionName(r: Region): string {
  return (LANG === "tr" && REGIONS_TR[r.id]?.name) || r.name
}

// Bölgenin tanıtım metni.
export function regionDescription(r: Region): string {
  return (LANG === "tr" && REGIONS_TR[r.id]?.description) || r.description
}

// Bölgenin tek cümlelik "neden ilginç" notu (D'nin teaser alanı).
export function regionTeaser(r: Region): string {
  return (LANG === "tr" && REGIONS_TR[r.id]?.teaser) || r.teaser || ""
}

// Ölçümün veri dönemiyle ilgili notu (ör. yağış verisi Eylül 2025'te bitiyor); yoksa boş.
export function variablePeriodNote(v: Variable): string {
  return (LANG === "tr" ? VARIABLES_TR[v.id]?.periodNote : undefined) ?? v.period_note ?? ""
}

// Ölçümün (değişkenin) ekranda gösterilecek adı.
export function variableName(v: Variable): string {
  return (LANG === "tr" && VARIABLES_TR[v.id]?.name) || v.name
}

// Ölçümün birimi (ör. "mm/month" yerine "mm/ay").
export function variableUnit(v: Variable): string {
  return (LANG === "tr" && VARIABLES_TR[v.id]?.unit) || v.unit
}

// Ölçümün tek cümlelik sade açıklaması.
export function variableShort(v: Variable): string {
  return (LANG === "tr" && VARIABLES_TR[v.id]?.short) || v.short_description
}

// Sözlükten bir terimin açıklamasını bulan yardımcı fonksiyon üretir
// (büyük/küçük harf farkını önemsemez). Türkçe modda önce Türkçe sözlüğe bakar.
export function makeTermHelp(glossary: Record<string, string>) {
  const backend = new Map(Object.entries(glossary).map(([k, v]) => [k.toLowerCase(), v]))
  return (term: string): string | undefined => {
    const key = term.toLowerCase()
    return (LANG === "tr" && GLOSSARY_TR[key]) || backend.get(key)
  }
}

export type Trend = "up" | "down" | "flat"

// Sonucu üç duruma indirger: anlamlı artış, anlamlı azalış ya da belirgin değişim yok.
export function trendKind(r: { significant: boolean; direction: string }): Trend {
  if (!r.significant) return "flat"
  return r.direction === "increasing" ? "up" : "down"
}

// Trend sonucunu sade dille anlatan cümleler üretir ("Bu ne demek?" kutusu için).
// İngilizce modda B'nin interpret() metni kullanılır; Türkçe modda cümleler
// buradaki kalıplarla, sonuçtaki sayılardan kurulur. B'nin yaklaşımına uyar:
// yön, hız ve anlamlılık Sen eğiminden / mevsimsel Mann-Kendall testinden gelir;
// sıcaklık gibi değişkenlerde yüzde değişim gösterilmez (showPercent=false).
export function explain(
  result: TrendResult,
  variable: Variable,
  region: Region,
  backendText: string,
  showPercent = true,
): string[] {
  if (LANG !== "tr") return [backendText]

  const unit = variableUnit(variable)
  const name = variableName(variable).toLocaleLowerCase("tr")
  const sen = result.sen_slope_per_decade
  const pct = showPercent ? result.percent_change_per_decade : null
  const pctText = pct !== null ? ` (yaklaşık %${fmt(Math.abs(pct), 1)})` : ""
  const years = Math.round(result.n_years)
  const total = (sen * result.n_years) / 10
  const where = `${regionName(region)} için`
  const p = result.mk_p < 0.001 ? "p < 0,001" : `p = ${fmt(result.mk_p, 3)}`

  const lines: string[] = []
  if (result.significant) {
    lines.push(
      `${where} ${name} her 10 yılda ortalama ${fmt(Math.abs(sen))} ${unit} ` +
        `${sen > 0 ? "artıyor" : "azalıyor"}${pctText}.`,
      `${result.start_year}–${result.end_year} arasındaki ${years} yılda bu, toplamda yaklaşık ` +
        `${fmt(total, 2, true)} ${unit} değişim demek.`,
      `Bu değişim istatistiksel olarak anlamlı (${p}): sadece yıldan yıla rastgele ` +
        "dalgalanmayla açıklanması çok düşük bir ihtimal.",
    )
  } else {
    lines.push(
      sen === 0
        ? `${where} ${name} ${result.start_year}–${result.end_year} arasında belirgin bir yön göstermiyor.`
        : `${where} ${name} ${result.start_year}–${result.end_year} arasında 10 yılda yaklaşık ` +
            `${fmt(Math.abs(sen))} ${unit} hafif bir ${sen > 0 ? "artış" : "azalış"} eğilimi gösteriyor${pctText}.`,
      `Ancak bu değişim henüz istatistiksel olarak anlamlı değil (${p}): yıldan yıla doğal ` +
        "iniş çıkışlardan ayırt edilemiyor.",
    )
    // B: years_needed_estimate = anlamlılık için gereken TOPLAM kayıt uzunluğu (yıl), kaba tahmin.
    const needed = result.years_needed_estimate
    if (needed !== null && needed > result.n_years && needed < 200) {
      lines.push(
        `Mevcut hız sürerse, net bir sonuç için toplamda kabaca ${Math.round(needed)} yıllık veri ` +
          `gerekebilir (şu an yaklaşık ${years} yıl var; bu kaba bir tahmindir).`,
      )
    } else if (needed !== null && needed >= 200) {
      lines.push("Mevcut hızla bir eğilim fark edebilmek için çok daha uzun bir kayıt gerekirdi.")
    }
  }
  lines.push("Not: Bu bir eğilim ölçümüdür; değişimin nedenini tek başına göstermez.")
  return lines
}

// ---------------------------------------------------------------------------
// Detective Mode, Case Files and Compare content
// ---------------------------------------------------------------------------

const THEMES_TR: Record<string, { label: string; blurb: string }> = {
  drought: { label: "Kuruyor mu?", blurb: "Toprak, yağış ve sıcaklıkta kuraklık izlerini ara." },
  warming: { label: "Isınıyor mu?", blurb: "Hava sıcaklığında uzun dönemli bir artış var mı, bul." },
  water: { label: "Suya ne oluyor?", blurb: "Yağmur ve topraktaki su miktarı nasıl değişiyor, incele." },
}

const THEMES_EN_BLURB: Record<string, string> = {
  drought: "Look for signs of drought in soil, rain and temperature.",
  warming: "Find out whether air temperature shows a long-term rise.",
  water: "See how rain and soil water are changing.",
}

// Temanın ekranda gösterilecek sorusu (ör. "Kuruyor mu?").
export function themeLabel(key: string, backendLabel: string): string {
  return (LANG === "tr" && THEMES_TR[key]?.label) || backendLabel
}

// Tema kartının altındaki kısa açıklama.
export function themeBlurb(key: string): string {
  return (LANG === "tr" ? THEMES_TR[key]?.blurb : THEMES_EN_BLURB[key]) ?? ""
}

// Theme reasons per (theme, variable), from D's catalog themes[].reasons.
const REASONS_TR: Record<string, string> = {
  "drought:soil_moisture": "Kuraklık ilk önce toprak neminde kendini gösterir.",
  "drought:precip": "Daha az yağış, bir bölgenin kurumasının en doğrudan yoludur.",
  "drought:temp":
    "Daha sıcak hava topraktan ve bitkilerden daha fazla su çeker; yağış aynı kalsa bile sıcaklık bir bölgeyi kurutabilir.",
  "warming:temp": "Hava sıcaklığı, ısınmanın en doğrudan işaretidir.",
  "water:precip": "Bir bölgenin suyu yağmur ve kardan gelir.",
  "water:soil_moisture": "Toprak nemi, o suyun ne kadarının bitkilerin ulaşabileceği yerde kaldığını gösterir.",
}

// Bir önerinin gerekçesi. D'nin suggest() fonksiyonu "temanın gerekçesi + bölgenin
// teaser'ı" birleştirir; Türkçe modda aynısı Türkçe parçalarla kurulur.
export function reasonText(theme: string, variableId: string, region: Region, backendReason: string): string {
  const reason = LANG === "tr" ? REASONS_TR[`${theme}:${variableId}`] : undefined
  return reason ? `${reason} ${regionTeaser(region)}`.trim() : backendReason
}

const CASES_TR: Record<string, { title: string; story: string }> = {
  konya_drying: {
    title: "Vaka 1: Konya kuruyor mu?",
    story:
      "Konya Kapalı Havzası'nda kuyular giderek daha derine kazılıyor ve tarlalarda obruklar açılıyor. " +
      "Peki toprağın kendisi gerçekten kuruyor mu, yoksa birkaç kötü yıldan sonra mı öyle hissediliyor? " +
      "25 yıllık NASA verisine bak ve kendin karar ver.",
  },
  van_warming: {
    title: "Vaka 2: Van Gölü havzası ısınıyor mu?",
    story:
      "Van Gölü çevresinde kışlar uzun ve karlı geçer; göl her bahar eriyen kara bağlıdır. " +
      "Daha sıcak bir havza daha az kar ve daha erken erime demek olabilir. " +
      "Ama hava son 25 yılda gerçekten ısındı mı, yoksa birkaç ılık kış mı öyle gösteriyor? Kararı veriye bırak.",
  },
  different_climates_same_story: {
    title: "Vaka 3: Çok farklı iklimler, aynı hikâye mi?",
    story:
      "Konya ovası kuru ve güneşli; Doğu Karadeniz'in dağları ise iki kattan fazla yağış alır, çay bahçeleri ve ormanlarla kaplıdır. " +
      "Topraklarının bambaşka hikâyeler anlatmasını bekleyebilirsin. İkisini yan yana koy ve öyle olup olmadığına bak.",
  },
  konya_rain_or_heat: {
    title: "Vaka 4: Yağmur mu, sıcak mı? Suçlu hangisi?",
    story:
      "Toprak iki nedenle kuruyabilir: üzerine daha az su düşer ya da daha sıcak hava ondan daha fazla su çeker. " +
      "Konya'da iki şüpheli de listede. Yağmurla başla, sonra sıcaklığı sorgula ve kanıtların hangi şüpheliye daha çok uyduğunu gör. " +
      "Unutma: bir eğilim bir şüpheliyi daha olası ya da daha az olası kılabilir, ama tek başına değişime neyin yol açtığını kanıtlayamaz.",
  },
}

// Vakanın başlığı (Türkçe modda çeviri, bilinmeyen vakada backend metni).
export function caseTitle(c: { id: string; title: string }): string {
  return (LANG === "tr" && CASES_TR[c.id]?.title) || c.title
}

// Vakanın giriş hikâyesi.
export function caseStory(c: { id: string; story: string }): string {
  return (LANG === "tr" && CASES_TR[c.id]?.story) || c.story
}

// Turkish templates for D's hint rules, keyed "variable|direction|significant"
// exactly as in catalog.json hints ("*" = any). {region} and {compare_region}
// are filled with Turkish region names.
const HINTS_TR: Record<string, string> = {
  "*|no change|true":
    "Test anlamlı bir eğilim gösteriyor ama tahmini hız neredeyse sıfır. Sonuca varmadan önce grafiğe dikkatle bak.",
  "soil_moisture|decreasing|true":
    "🕵️ İpucu bulundu! {region} için toprak kuruyor. Sebep daha az yağış mı, daha çok sıcaklık mı? Sıradaki adım: yağışa bak.",
  "soil_moisture|increasing|true":
    "🕵️ İlginç: {region} için toprak nemleniyor. Daha fazla yağış mı düşüyor? Sıradaki adım: yağışa bak.",
  "soil_moisture|*|false":
    "Toprak neminde henüz anlamlı bir eğilim yok; yıldan yıla doğal dalgalanmalar bir değişimi gizliyor olabilir. Farklı bir hikâye için {compare_region} ile karşılaştır.",
  "precip|decreasing|true":
    "🕵️ İpucu bulundu! {region} için daha az yağış düşüyor. Toprak bunu hissediyor mu? Sıradaki adım: toprak nemine bak.",
  "precip|increasing|true":
    "🕵️ {region} için daha fazla yağış düşüyor. Ülkenin geri kalanı da aynısını mı yaşıyor? {compare_region} ile karşılaştır.",
  "precip|*|false":
    "{region} için yağış belirgin şekilde değişmiyor; yıldan yıla doğal iniş çıkışları büyük. O zaman toprak kuruyorsa arkasında başka ne olabilir? Sıcaklığa bak.",
  "temp|increasing|true":
    "🕵️ İpucu bulundu! {region} için hava ısınıyor. Sıcak hava topraktan ve bitkilerden daha fazla su çeker; sıradaki adım: toprak nemi.",
  "temp|decreasing|true":
    "{region} için hava serinliyor; bu, dünyanın çoğunda görülen ısınmaya ters. Kontrol etmek için {compare_region} ile karşılaştır.",
  "temp|*|false":
    "Henüz anlamlı bir sıcaklık eğilimi yok; 25 yıl karar vermek için yeterli mi? {compare_region} ile karşılaştır.",
  "*|*|*":
    "Henüz net bir ipucu yok; {compare_region} ile karşılaştırmayı dene ya da 25 yılın yeterli olup olmadığını düşün.",
}

// D'nin next_step() kuralını arayüzde tekrarlar (D'nin modülü bunun mümkün olduğunu
// belgeliyor): katalogdaki ilk eşleşen kural; "*" her değerle eşleşir. Türkçe modda
// o kuralın çevirisini, İngilizce modda D'nin metnini döndürür.
export function hintText(
  hints: HintRule[],
  result: TrendResult,
  variableId: string,
  region: Region,
  compare: Region | undefined,
  backendText: string,
): string {
  if (LANG !== "tr") return backendText
  const ok = (rule: string | boolean, actual: string | boolean) => rule === "*" || rule === actual
  const rule = hints.find(
    (h) => ok(h.variable_id, variableId) && ok(h.direction, result.direction) && ok(h.significant, result.significant),
  )
  const template = rule && HINTS_TR[`${rule.variable_id}|${rule.direction}|${rule.significant}`]
  if (!template) return backendText
  return template
    .replaceAll("{region}", regionName(region))
    .replaceAll("{compare_region}", compare ? regionName(compare) : "")
}

// Karşılaştırma özet cümlesi: aynı yönde mi, zıt yönde mi, hangisi anlamlı.
// İngilizce modda B'nin compare_trends() özeti kullanılır.
export function compareSummary(
  a: TrendResult,
  b: TrendResult,
  regionA: Region,
  regionB: Region,
  variable: Variable,
  backendSummary: string,
): string[] {
  if (LANG !== "tr") return [backendSummary]
  const name = variableName(variable).toLocaleLowerCase("tr")
  const verb = (r: TrendResult) =>
    r.direction === "increasing" ? "artıyor" : r.direction === "decreasing" ? "azalıyor" : "değişmiyor"
  const nameA = regionName(regionA)
  const nameB = regionName(regionB)
  const lines =
    a.direction === b.direction && a.direction !== "no change"
      ? [`${nameA} ve ${nameB} aynı yönde: ikisinde de ${name} ${verb(a)}.`]
      : [`Zıt hikâyeler: ${nameA} için ${name} ${verb(a)}, ama ${nameB} için ${verb(b)}.`]
  if (a.significant && b.significant) {
    lines.push("İki değişim de istatistiksel olarak anlamlı.")
  } else if (a.significant || b.significant) {
    lines.push(`Ancak sadece ${a.significant ? nameA : nameB} için değişim istatistiksel olarak anlamlı; diğerinde henüz doğal dalgalanmadan ayırt edilemiyor.`)
  } else {
    lines.push("İki değişim de henüz istatistiksel olarak anlamlı değil; dikkatli yorumlamak gerek.")
  }
  return lines
}
