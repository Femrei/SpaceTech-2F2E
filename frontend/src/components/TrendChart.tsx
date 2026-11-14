import type { ReactNode } from "react"
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import type { Point, Region, TrendResult, Variable } from "@/lib/api"
import { LANG, fmt, t } from "@/lib/i18n"

// Renk körlüğüne uygun turuncu/mavi çifti. Anlam hiçbir zaman sadece renkle
// verilmez: trend yönü ve anlamlılık her zaman yazıyla da gösterilir.
export const COLOR_INCREASING = "#D55E00"
export const COLOR_DECREASING = "#0072B2"
export const COLOR_NOT_SIGNIFICANT = "#8C8C8C"

// Trendin rengini seçer: artan = turuncu, azalan = mavi, anlamsız = gri.
export function trendColor(r: TrendResult): string {
  if (!r.significant) return COLOR_NOT_SIGNIFICANT
  return r.direction === "increasing" ? COLOR_INCREASING : COLOR_DECREASING
}

// Trendi yazıyla anlatan kısa etiket üretir (ör. "▼ azalıyor (anlamlı)").
export function trendLabel(r: TrendResult): string {
  const up = r.direction === "increasing"
  return `${up ? "▲" : "▼"} ${up ? t("increasing") : t("decreasing")} (${
    r.significant ? t("sigShort") : t("notSigShort")
  })`
}

// "2010-07-01" gibi bir tarihi seçili dilde "Tem 2010" biçimine çevirir.
function monthLabel(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString(LANG === "tr" ? "tr-TR" : "en-US", {
    month: "short",
    year: "numeric",
  })
}

interface ChartRow extends Point {
  band: [number, number] | null
}

// Fare grafiğin üzerine gelince çıkan bilgi kutusu: o ayın tüm değerlerini
// (ham değer, ortalama, anomali, trend) birimiyle birlikte listeler.
function PointTooltip({ active, payload, unit }: {
  active?: boolean
  payload?: { payload: ChartRow }[]
  unit: string
}) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  const lines: [string, number | null, boolean][] = [
    [t("monthlyValue"), row.value, false],
    [t("movingAvg"), row.smooth, false],
    [t("anomaly"), row.anomaly, true],
    [t("trend"), row.trend, true],
  ]
  return (
    <div className="rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="mb-1 font-medium">{monthLabel(row.date)}</div>
      {lines.map(([label, v, signed]) =>
        v === null ? null : (
          <div key={label} className="flex justify-between gap-4">
            <span className="text-muted-foreground">{label}</span>
            <span className="font-mono tabular-nums">
              {fmt(v, 2, signed)} {unit}
            </span>
          </div>
        ),
      )}
    </div>
  )
}

// Grafiğin altındaki açıklama satırı (lejant): her çizginin örnek işareti + adı.
function Legend({ items }: { items: { label: string; swatch: ReactNode }[] }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
      {items.map((it) => (
        <span key={it.label} className="inline-flex items-center gap-1.5">
          {it.swatch}
          {it.label}
        </span>
      ))}
    </div>
  )
}

// Explore'daki ana grafik (iki panel, x ekseni ve fare takibi ortak):
//   Üst panel: ham aylık değerler (ince, soluk) + 12 aylık hareketli ortalama (kalın)
//   Alt panel: anomaliler (çubuk), yelpaze şeklinde %95 güven bandı, kesikli trend çizgisi
// Başlıkta "Bölge · Değişken", eksenlerde birim gösterilir.
export function TrendChart({ points, result, variable, region }: {
  points: Point[]
  result: TrendResult
  variable: Variable
  region: Region
}) {
  const unit = variable.unit
  const color = trendColor(result)
  const rows: ChartRow[] = points.map((p) => ({
    ...p,
    band: p.ci_low !== null && p.ci_high !== null ? [p.ci_low, p.ci_high] : null,
  }))
  // Her 5 yılda bir (Ocak ayı) x ekseninde yıl etiketi göster.
  const yearTicks = rows
    .map((r) => r.date)
    .filter((d) => d.endsWith("-01-01") && Number(d.slice(0, 4)) % 5 === 0)

  const config = {
    value: { label: t("monthlyValue"), color: "var(--muted-foreground)" },
    smooth: { label: t("movingAvg"), color: "var(--foreground)" },
    anomaly: { label: t("anomaly"), color: "var(--muted-foreground)" },
    trend: { label: t("trend"), color },
  } satisfies ChartConfig

  const xAxis = (showTicks: boolean) => (
    <XAxis
      dataKey="date"
      ticks={yearTicks}
      tickFormatter={(d: string) => d.slice(0, 4)}
      tick={showTicks}
      tickLine={false}
      axisLine={false}
      height={showTicks ? 24 : 4}
    />
  )
  const yLabel = (text: string) => ({
    value: text,
    angle: -90,
    position: "insideLeft" as const,
    style: { textAnchor: "middle" as const, fill: "var(--muted-foreground)", fontSize: 12 },
  })

  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold">
        {region.name} · {variable.name}
      </h3>

      <p className="text-sm text-muted-foreground">{t("monthlyValues")}</p>
      <ChartContainer config={config} className="aspect-auto h-[240px] w-full">
        <LineChart data={rows} syncId="trend" margin={{ left: 12, right: 8, top: 4 }}>
          <CartesianGrid vertical={false} />
          {xAxis(false)}
          <YAxis width={56} tickLine={false} axisLine={false} label={yLabel(`${variable.name} (${unit})`)} />
          <Tooltip content={<PointTooltip unit={unit} />} />
          <Line dataKey="value" stroke="var(--color-value)" strokeOpacity={0.5} strokeWidth={1} dot={false} isAnimationActive={false} />
          <Line dataKey="smooth" stroke="var(--color-smooth)" strokeOpacity={0.75} strokeWidth={2.5} dot={false} isAnimationActive={false} />
        </LineChart>
      </ChartContainer>

      <p className="text-sm text-muted-foreground">
        {t("anomaliesAndTrend", { label: trendLabel(result) })}
      </p>
      <ChartContainer config={config} className="aspect-auto h-[220px] w-full">
        <ComposedChart data={rows} syncId="trend" margin={{ left: 12, right: 8, top: 4 }} barCategoryGap={0}>
          <CartesianGrid vertical={false} />
          {xAxis(true)}
          <YAxis width={56} tickLine={false} axisLine={false} label={yLabel(`${t("anomaly")} (${unit})`)} />
          <Tooltip content={<PointTooltip unit={unit} />} />
          <ReferenceLine y={0} stroke="var(--border)" />
          <Bar dataKey="anomaly" fill="var(--color-anomaly)" fillOpacity={0.45} isAnimationActive={false} />
          <Area dataKey="band" stroke="none" fill={color} fillOpacity={0.28} isAnimationActive={false} />
          <Line dataKey="trend" stroke={color} strokeWidth={3} strokeDasharray="8 5" dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ChartContainer>

      <Legend
        items={[
          {
            label: `${t("trend")}: ${fmt(result.slope_per_decade, 2, true)} ${t("perDecadeUnit", { unit })}, ${trendLabel(result)}`,
            swatch: <span className="inline-block w-5 border-t-[3px] border-dashed" style={{ borderColor: color }} />,
          },
          {
            label: t("ciBand"),
            swatch: <span className="inline-block h-2.5 w-5 rounded-sm" style={{ background: color, opacity: 0.28 }} />,
          },
          {
            label: t("anomaly"),
            swatch: <span className="inline-block h-2.5 w-2.5 rounded-sm bg-muted-foreground/45" />,
          },
          {
            label: t("movingAvg"),
            swatch: <span className="inline-block w-5 border-t-[2.5px] border-foreground/75" />,
          },
          {
            label: t("monthlyValue"),
            swatch: <span className="inline-block w-5 border-t border-muted-foreground/50" />,
          },
        ]}
      />
    </div>
  )
}
