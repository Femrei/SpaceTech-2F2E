import type { ReactNode } from "react"
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import type { Point, TrendResult } from "@/lib/api"
import { trendKind } from "@/lib/content"
import { LANG, fmt, t } from "@/lib/i18n"
import { TREND_COLOR } from "@/lib/trendStyle"

export type ChartView = "simple" | "detailed"

// "2010-07-01" gibi bir tarihi seçili dilde "Tem 2010" biçimine çevirir.
function monthLabel(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString(LANG === "tr" ? "tr-TR" : "en-US", {
    month: "short",
    year: "numeric",
  })
}

interface Row {
  date: string
  value: number | null
  smooth: number | null
  anomaly: number | null
  trend: number | null
  band: [number, number] | null
}

// Fare grafiğin üzerine gelince çıkan bilgi kutusu: o ayın değerlerini birimiyle listeler.
// Basit görünümde aylık değer + ortalama + eğilim, detaylıda normalden fark + eğilim.
function RowTooltip({ active, payload, unit, view }: {
  active?: boolean
  payload?: { payload: Row }[]
  unit: string
  view: ChartView
}) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  const lines: [string, number | null, boolean][] =
    view === "simple"
      ? [[t("monthlyValue"), row.value, false], [t("movingAvg"), row.smooth, false], [t("trendLine"), row.trend, false]]
      : [[t("anomaly"), row.anomaly, true], [t("trendLine"), row.trend, true]]
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

// Panodaki ana grafik. İki görünümü var:
//   Basit:   aylık değerler (ince gri) + 12 aylık ortalama (kalın) + uzun dönem
//            eğilim (kesikli, renkli) ve belirsizlik aralığı; hepsi gerçek birimde.
//   Detaylı: her ayın normalden farkı (anomali, çubuk) + eğilim + belirsizlik aralığı.
// Eğilim çizgisi anomaliler üzerinden hesaplanır; basit görünümde uzun dönem
// ortalama eklenerek gerçek değerlerin seviyesine taşınır.
export function TrendChart({ points, result, unit, view }: {
  points: Point[]
  result: TrendResult
  unit: string
  view: ChartView
}) {
  const color = TREND_COLOR[trendKind(result)]
  const shift = view === "simple" ? result.mean_value : 0
  const rows: Row[] = points.map((p) => ({
    date: p.date,
    value: p.value,
    smooth: p.smooth,
    anomaly: p.anomaly,
    trend: p.trend === null ? null : p.trend + shift,
    band: p.ci_low !== null && p.ci_high !== null ? [p.ci_low + shift, p.ci_high + shift] : null,
  }))
  // Her 5 yılda bir (Ocak ayı) x ekseninde yıl etiketi göster.
  const yearTicks = rows
    .map((r) => r.date)
    .filter((d) => d.endsWith("-01-01") && Number(d.slice(0, 4)) % 5 === 0)

  const config = {
    value: { label: t("monthlyValue"), color: "var(--muted-foreground)" },
    smooth: { label: t("movingAvg"), color: "var(--foreground)" },
    anomaly: { label: t("anomaly"), color: "var(--muted-foreground)" },
    trend: { label: t("trendLine"), color },
  } satisfies ChartConfig

  const trendSwatch = <span className="inline-block w-5 border-t-[3px] border-dashed" style={{ borderColor: color }} />
  const bandSwatch = <span className="inline-block h-2.5 w-5 rounded-sm" style={{ background: color, opacity: 0.3 }} />

  return (
    <div className="space-y-3">
      <ChartContainer config={config} className="aspect-auto h-[300px] w-full sm:h-[340px]">
        <ComposedChart data={rows} margin={{ left: 0, right: 8, top: 16 }} barCategoryGap={0}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="date" ticks={yearTicks} tickFormatter={(d: string) => d.slice(0, 4)} tickLine={false} axisLine={false} />
          <YAxis
            width={48}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => fmt(v, 0)}
            label={{ value: unit, position: "top", offset: 6, style: { fill: "var(--muted-foreground)", fontSize: 11 } }}
          />
          <Tooltip content={<RowTooltip unit={unit} view={view} />} />
          {view === "simple" ? (
            <>
              <Line dataKey="value" stroke="var(--color-value)" strokeOpacity={0.45} strokeWidth={1} dot={false} isAnimationActive={false} />
              <Line dataKey="smooth" stroke="var(--color-smooth)" strokeOpacity={0.8} strokeWidth={2.5} dot={false} isAnimationActive={false} />
            </>
          ) : (
            <>
              <ReferenceLine y={0} stroke="var(--border)" />
              <Bar dataKey="anomaly" fill="var(--color-anomaly)" fillOpacity={0.45} isAnimationActive={false} />
            </>
          )}
          <Area dataKey="band" stroke="none" fill={color} fillOpacity={0.3} isAnimationActive={false} />
          <Line dataKey="trend" stroke={color} strokeWidth={3} strokeDasharray="8 5" dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ChartContainer>

      <Legend
        items={
          view === "simple"
            ? [
                { label: t("monthlyValue"), swatch: <span className="inline-block w-5 border-t border-muted-foreground/60" /> },
                { label: t("movingAvg"), swatch: <span className="inline-block w-5 border-t-[2.5px] border-foreground/80" /> },
                { label: t("trendLine"), swatch: trendSwatch },
                { label: t("ciBand"), swatch: bandSwatch },
              ]
            : [
                { label: t("anomaly"), swatch: <span className="inline-block h-2.5 w-2.5 rounded-sm bg-muted-foreground/45" /> },
                { label: t("trendLine"), swatch: trendSwatch },
                { label: t("ciBand"), swatch: bandSwatch },
              ]
        }
      />
    </div>
  )
}
