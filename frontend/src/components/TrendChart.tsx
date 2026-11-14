import { useId, useState, type ReactNode } from "react"
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
  yearly?: boolean
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
  const title = row.yearly ? row.date.slice(0, 4) : monthLabel(row.date)
  const lines: [string, number | null, boolean][] =
    view === "simple"
      ? [[t("monthlyValue"), row.value, false], [t("movingAvg"), row.smooth, false], [t("trendLine"), row.trend, false]]
      : [[t("anomaly"), row.anomaly, true], [t("trendLine"), row.trend, true]]
  return (
    <div className="rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="mb-1 font-medium">{title}</div>
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

// Detaylı görünüm için aylık satırları yıllık ortalamaya indirger: her yıl için
// normalden ortalama fark, eğilim ve belirsizlik aralığı. En az 10 ayı olmayan
// yıllar atlanır. Yıllık ortalama aylık gürültüyü söndürür, eğilim seçilir hale gelir.
function yearlyRows(rows: Row[]): Row[] {
  const byYear = new Map<string, Row[]>()
  for (const r of rows) {
    const y = r.date.slice(0, 4)
    byYear.set(y, [...(byYear.get(y) ?? []), r])
  }
  const mean = (xs: (number | null)[]) => {
    const v = xs.filter((x): x is number => x !== null)
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
  }
  return [...byYear.entries()].map(([y, rs]) => {
    const anomalies = rs.map((r) => r.anomaly)
    const enough = anomalies.filter((a) => a !== null).length >= 10
    const lo = mean(rs.map((r) => r.band?.[0] ?? null))
    const hi = mean(rs.map((r) => r.band?.[1] ?? null))
    return {
      date: `${y}-07-01`,
      yearly: true,
      value: null,
      smooth: null,
      anomaly: enough ? mean(anomalies) : null,
      trend: mean(rs.map((r) => r.trend)),
      band: lo !== null && hi !== null ? [lo, hi] : null,
    }
  })
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
//   Basit:   12 aylık ortalama (kalın) + uzun dönem eğilim (kesikli, renkli) ve
//            belirsizlik aralığı; hepsi gerçek birimde. Ham aylık değerler
//            mevsimlerle çok iner çıktığı için varsayılan olarak gizli; kutucukla açılır.
//            Eksen veriye göre ölçeklenir (0'dan başlamaz), böylece eğilim görünür.
//   Detaylı: her yılın normalden ortalama farkı (anomali, çubuk) + eğilim + belirsizlik aralığı.
// Eğilim çizgisi anomaliler üzerinden hesaplanır; basit görünümde uzun dönem
// ortalama eklenerek gerçek değerlerin seviyesine taşınır.
export function TrendChart({ points, result, unit, view }: {
  points: Point[]
  result: TrendResult
  unit: string
  view: ChartView
}) {
  const [showMonthly, setShowMonthly] = useState(false)
  const toggleId = useId()
  const color = TREND_COLOR[trendKind(result)]
  const shift = view === "simple" ? result.mean_value : 0
  const monthly: Row[] = points.map((p) => ({
    date: p.date,
    value: p.value,
    smooth: p.smooth,
    anomaly: p.anomaly,
    trend: p.trend === null ? null : p.trend + shift,
    band: p.ci_low !== null && p.ci_high !== null ? [p.ci_low + shift, p.ci_high + shift] : null,
  }))
  const rows = view === "detailed" ? yearlyRows(monthly) : monthly
  // Her 5 yılda bir (Ocak ayı) x ekseninde yıl etiketi göster.
  const yearTicks = rows
    .map((r) => r.date)
    .filter((d) => (d.endsWith("-01-01") || d.endsWith("-07-01")) && Number(d.slice(0, 4)) % 5 === 0)
    .filter((d, i, all) => all.findIndex((x) => x.slice(0, 4) === d.slice(0, 4)) === i)

  const config = {
    value: { label: t("monthlyValue"), color: "var(--muted-foreground)" },
    smooth: { label: t("movingAvg"), color: "var(--foreground)" },
    anomaly: { label: t("anomaly"), color: "var(--foreground)" },
    trend: { label: t("trendLine"), color },
  } satisfies ChartConfig

  const trendSwatch = <span className="inline-block w-5 border-t-[3.5px] border-dashed" style={{ borderColor: color }} />
  const bandSwatch = <span className="inline-block h-2.5 w-5 rounded-sm" style={{ background: color, opacity: 0.3 }} />

  return (
    <div className="space-y-3">
      <ChartContainer config={config} className="aspect-auto h-[300px] w-full sm:h-[340px]">
        <ComposedChart data={rows} margin={{ left: 0, right: 8, top: 16 }} barCategoryGap={view === "detailed" ? "18%" : 0}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="date" ticks={yearTicks} tickFormatter={(d: string) => d.slice(0, 4)} tickLine={false} axisLine={false} />
          <YAxis
            width={48}
            domain={["auto", "auto"]}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => fmt(v, 0)}
            label={{ value: unit, position: "top", offset: 6, style: { fill: "var(--muted-foreground)", fontSize: 11 } }}
          />
          <Tooltip content={<RowTooltip unit={unit} view={view} />} />
          {view === "simple" ? (
            <>
              {showMonthly && (
                <Line dataKey="value" stroke="var(--color-value)" strokeOpacity={0.6} strokeWidth={1} dot={false} isAnimationActive={false} />
              )}
              <Line dataKey="smooth" stroke="var(--color-smooth)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
            </>
          ) : (
            <>
              <ReferenceLine y={0} stroke="var(--muted-foreground)" strokeOpacity={0.6} />
              <Bar dataKey="anomaly" fill="var(--color-anomaly)" fillOpacity={0.35} radius={[2, 2, 2, 2]} isAnimationActive={false} />
            </>
          )}
          {/* The trend is a straight line, so bridging months with missing data does not change it. */}
          <Area dataKey="band" stroke="none" fill={color} fillOpacity={0.25} connectNulls isAnimationActive={false} />
          <Line dataKey="trend" stroke={color} strokeWidth={3.5} strokeDasharray="10 6" dot={false} connectNulls isAnimationActive={false} />
        </ComposedChart>
      </ChartContainer>

      <Legend
        items={
          view === "simple"
            ? [
                ...(showMonthly
                  ? [{ label: t("monthlyValue"), swatch: <span className="inline-block w-5 border-t border-muted-foreground" /> }]
                  : []),
                { label: t("movingAvg"), swatch: <span className="inline-block w-5 border-t-[2.5px] border-foreground" /> },
                { label: t("trendLine"), swatch: trendSwatch },
                { label: t("ciBand"), swatch: bandSwatch },
              ]
            : [
                { label: t("anomalyYearly"), swatch: <span className="inline-block h-2.5 w-2.5 rounded-sm bg-foreground/35" /> },
                { label: t("trendLine"), swatch: trendSwatch },
                { label: t("ciBand"), swatch: bandSwatch },
              ]
        }
      />

      {view === "simple" && (
        <label htmlFor={toggleId} className="inline-flex min-h-6 cursor-pointer items-center gap-2 text-xs text-muted-foreground">
          <input
            id={toggleId}
            type="checkbox"
            className="size-4"
            checked={showMonthly}
            onChange={(e) => setShowMonthly(e.target.checked)}
          />
          {t("showMonthly")}
        </label>
      )}
    </div>
  )
}
