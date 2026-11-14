// Display content for regions, variables and glossary terms, plus the
// plain-language explanation of a trend result (owner: C).
//
// The backend (D's catalog, B's interpret()) provides English content. While
// LANG is "tr" we show the Turkish versions below instead, keyed by id, so the
// teammates' files never need to change. Unknown ids fall back to the backend.

import type { Region, TrendResult, Variable } from "@/lib/api"
import { LANG, fmt, fmtPct } from "@/lib/i18n"

const REGIONS_TR: Record<string, { name: string; description: string }> = {
  konya: {
    name: "Konya Kapalı Havzası",
    description:
      "İç Anadolu'da, suları denize ulaşmayan büyük bir havza. Türkiye'nin önemli tahıl bölgelerinden biri; tarım büyük ölçüde yeraltı suyuna dayanıyor.",
  },
  van: {
    name: "Van Gölü Havzası",
    description:
      "Doğu Anadolu'da, Türkiye'nin en büyük gölü olan Van Gölü'nün çevresi. Yüksek rakımlı, kışları uzun ve sert.",
  },
  black_sea: {
    name: "Doğu Karadeniz",
    description:
      "Türkiye'nin en çok yağış alan bölgesi. Dağlar kıyıya paralel uzanır ve denizden gelen nemli havayı yağışa çevirir.",
  },
}

const VARIABLES_TR: Record<string, { name: string; unit: string; short: string }> = {
  precip: {
    name: "Yağış",
    unit: "mm/ay",
    short: "Bir ayda yağan yağmur ve karın toplam miktarı.",
  },
  soil_moisture: {
    name: "Toprak nemi",
    unit: "kg/m²",
    short: "Toprağın üst 10 cm'sindeki su: bitkilerin kolayca ulaşabildiği su miktarı.",
  },
  temp: {
    name: "Hava sıcaklığı",
    unit: "°C",
    short: "Yerden 2 metre yükseklikteki ortalama hava sıcaklığı.",
  },
}

const GLOSSARY_TR: Record<string, string> = {
  "trend":
    "Bir ölçümün yıllar içindeki genel gidişatı; aylık iniş çıkışlar ayıklandıktan sonra kalan yön.",
  "anomaly":
    "Bir ayın, aynı takvim ayının normalinden ne kadar saptığı. Bir Temmuz ortalama Temmuzlardan 1 °C sıcaksa anomali +1 °C'dir.",
  "seasonal cycle": "Her yıl tekrarlanan mevsimsel iniş çıkış (yazın sıcak, kışın soğuk gibi).",
  "p-value":
    "Gerçekte hiçbir değişim yokken, sırf şans eseri bu kadar güçlü bir eğilim görme ihtimali. 0,05'in altındaysa sonuç anlamlı sayılır.",
  "statistically significant":
    "Gözlenen eğilimin rastgele dalgalanmayla açıklanması çok düşük ihtimal demektir (burada p < 0,05).",
  "mann-kendall test":
    "Değerlerin zaman içinde sürekli artma ya da azalma eğiliminde olup olmadığını, düz bir çizgi varsaymadan kontrol eden istatistiksel test.",
  "sen's slope":
    "Aykırı değerlerden az etkilenen bir eğim tahmini: tüm nokta çiftleri arasındaki eğimlerin ortancası.",
  "confidence interval":
    "Gerçek eğimin %95 ihtimalle içinde bulunduğu aralık. Aralık ne kadar darsa tahmin o kadar kesindir.",
  "per decade": "Mevcut hız devam ederse 10 yılda oluşacak değişim.",
  "area-averaged": "Her ay için bölgenin tamamının ortalaması alınarak tek bir değer elde edilir.",
}

// Bölgenin ekranda gösterilecek adı (Türkçe modda çeviri, yoksa backend'deki ad).
export function regionName(r: Region): string {
  return (LANG === "tr" && REGIONS_TR[r.id]?.name) || r.name
}

// Bölgenin kısa tanıtım metni.
export function regionDescription(r: Region): string {
  return (LANG === "tr" && REGIONS_TR[r.id]?.description) || r.description
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
// buradaki kalıplarla, sonuçtaki sayılardan kurulur.
export function explain(
  result: TrendResult,
  variable: Variable,
  region: Region,
  backendText: string,
): string[] {
  if (LANG !== "tr") return [backendText]

  const unit = variableUnit(variable)
  const name = variableName(variable)
  const verb = result.direction === "increasing" ? "artıyor" : "azalıyor"
  const pct = result.percent_change_per_decade
  const years = result.end_year - result.start_year + 1
  const total = (result.slope_per_decade * years) / 10

  const lines = [
    `${regionName(region)} için ${name.toLocaleLowerCase("tr")} her 10 yılda ortalama ` +
      `${fmt(Math.abs(result.slope_per_decade))} ${unit} ${verb}` +
      (pct !== null ? ` (yaklaşık ${fmtPct(Math.abs(pct))}).` : "."),
    `${result.start_year}–${result.end_year} arasındaki ${years} yılda bu, toplamda yaklaşık ` +
      `${fmt(total, 2, true)} ${unit} değişim demek.`,
  ]
  if (result.significant) {
    lines.push(
      `Bu değişim istatistiksel olarak anlamlı (p = ${fmt(result.mk_p, 3)}): ` +
        "sadece yıldan yıla rastgele dalgalanmayla açıklanması çok düşük bir ihtimal.",
    )
  } else {
    lines.push(
      `Bu değişim henüz istatistiksel olarak anlamlı değil (p = ${fmt(result.mk_p, 2)}): ` +
        "yıldan yıla doğal iniş çıkışlardan ayırt edilemiyor.",
    )
    if (result.years_needed_estimate) {
      lines.push(
        `Mevcut hız sürerse, net bir sonuç için kabaca ${result.years_needed_estimate} yıllık veri gerekebilir.`,
      )
    }
  }
  lines.push("Not: Bu bir eğilim ölçümüdür; değişimin nedenini tek başına göstermez.")
  return lines
}
