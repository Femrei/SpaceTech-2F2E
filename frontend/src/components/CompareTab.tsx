import { useState } from "react"
import { ArrowLeftRightIcon, CircleCheckIcon, CircleDashedIcon, EqualIcon } from "lucide-react"
import { CartesianGrid, ComposedChart, Line, ReferenceLine, Tooltip, XAxis, YAxis } from "recharts"

import { LoadingPanels, Picker, Warning } from "@/components/Common"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, type ChartConfig } from "@/components/ui/chart"
import type { ComparePoint, Meta, Region, TrendResult, Variable } from "@/lib/api"
import { compareSummary, regionName, trendKind, variableName, variableShort, variableUnit } from "@/lib/content"
import { LANG, fmt, fmtP, t } from "@/lib/i18n"
import { TREND_ICON, TREND_TEXT, trendText } from "@/lib/trendStyle"
import { useComparison } from "@/lib/useAnalysis"

// İki bölgeyi ayırt etmek için renk körlüğüne uygun (Okabe-Ito) iki renk; değerleri
// index.css'te. Trend yönü renkleri (turuncu/mavi) ile karışmasın diye farklı tonlar.
const COLOR_A = "var(--region-a)"
const COLOR_B = "var(--region-b)"

// Fare grafiğin üzerine gelince iki bölgenin o ayki değerlerini gösteren kutu.
function CompareTooltip({ active, payload, unit, nameA, nameB }: {
  active?: boolean
  payload?: { payload: ComparePoint }[]
  unit: string
  nameA: string
  nameB: string
}) {
  const row = payload?.[0]?.payload
  if (!active || !row) return null
  const date = new Date(`${row.date}T00:00:00`).toLocaleDateString(LANG === "tr" ? "tr-TR" : "en-US", {
    month: "short",
    year: "numeric",
  })
  return (
    <div className="rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl">
      <div className="mb-1 font-medium">{date}</div>
      {([[nameA, row.a, COLOR_A], [nameB, row.b, COLOR_B]] as const).map(([name, v, color]) =>
        v === null ? null : (
          <div key={name} className="flex items-center justify-between gap-4">
            <span className="inline-flex items-center gap-1.5 text-muted-foreground">
              <span className="size-2 rounded-full" style={{ background: color }} />
              {name}
            </span>
            <span className="font-mono tabular-nums">{fmt(v, 2, true)} {unit}</span>
          </div>
        ),
      )}
    </div>
  )
}

// Bir bölgenin özet kartı: renk işareti + adı, yön oku + yazısı, 10 yıllık
// değişim ve anlamlılık.
function RegionSummary({ region, result, unit, color }: {
  region: Region
  result: TrendResult
  unit: string
  color: string
}) {
  const kind = trendKind(result)
  const Icon = TREND_ICON[kind]
  return (
    <Card size="sm">
      <CardContent className="space-y-1.5">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <span className="h-1 w-5 rounded-full" style={{ background: color }} />
          {regionName(region)}
        </div>
        <div className="flex items-center gap-1.5 text-lg font-semibold" style={{ color: TREND_TEXT[kind] }}>
          <Icon className="size-5" />
          {trendText(kind)}
        </div>
        <div className="text-sm">
          {fmt(result.sen_slope_per_decade, 2, true)} {t("perDecadeUnit", { unit })}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          {result.significant ? (
            <CircleCheckIcon className="size-3.5 text-emerald-600 dark:text-emerald-400" />
          ) : (
            <CircleDashedIcon className="size-3.5" />
          )}
          {result.significant ? t("significant") : t("notSignificant")} · {fmtP(result.mk_p)}
        </div>
      </CardContent>
    </Card>
  )
}

// İki bölgenin karşılaştırma görünümü (Karşılaştır sekmesi ve iki bölgeli vakalar
// bunu kullanır): iki bölge özeti, ortak grafik ve "aynı yön / zıt yön" özeti.
export function CompareView({ meta, variableId, regionA, regionB }: {
  meta: Meta
  variableId: string
  regionA: string
  regionB: string
}) {
  const variable = meta.variables.find((v) => v.id === variableId) as Variable
  const a = meta.regions.find((r) => r.id === regionA) as Region
  const b = meta.regions.find((r) => r.id === regionB) as Region
  const ok = regionA !== regionB
  const state = useComparison(variableId, regionA, regionB, ok)

  if (!ok) return <Warning>{t("sameRegion")}</Warning>
  if (!state) return <LoadingPanels />
  if (state.error || !state.data) return <Warning>{state.error}</Warning>

  const { data } = state
  const unit = variableUnit(variable)
  const opposite = !data.comparison.same_direction
  const yearTicks = data.points
    .map((p) => p.date)
    .filter((d) => d.endsWith("-01-01") && Number(d.slice(0, 4)) % 5 === 0)
  const config = {
    a: { label: regionName(a), color: COLOR_A },
    b: { label: regionName(b), color: COLOR_B },
  } satisfies ChartConfig

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <RegionSummary region={a} result={data.result_a} unit={unit} color={COLOR_A} />
        <RegionSummary region={b} result={data.result_b} unit={unit} color={COLOR_B} />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{variableName(variable)}: {t("compareChartTitle")}</CardTitle>
            <CardDescription>{t("compareChartDesc")}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <ChartContainer config={config} className="aspect-auto h-[300px] w-full sm:h-[340px]">
              <ComposedChart data={data.points} margin={{ left: 0, right: 8, top: 16 }}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="date" ticks={yearTicks} tickFormatter={(d: string) => d.slice(0, 4)} tickLine={false} axisLine={false} />
                <YAxis
                  width={48}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => fmt(v, 1)}
                  label={{ value: unit, position: "top", offset: 6, style: { fill: "var(--muted-foreground)", fontSize: 11 } }}
                />
                <Tooltip content={<CompareTooltip unit={unit} nameA={regionName(a)} nameB={regionName(b)} />} />
                <ReferenceLine y={0} stroke="var(--border)" />
                <Line dataKey="a" stroke={COLOR_A} strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line dataKey="b" stroke={COLOR_B} strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line dataKey="trend_a" stroke={COLOR_A} strokeWidth={3} strokeDasharray="8 5" dot={false} isAnimationActive={false} />
                <Line dataKey="trend_b" stroke={COLOR_B} strokeWidth={3} strokeDasharray="8 5" dot={false} isAnimationActive={false} />
              </ComposedChart>
            </ChartContainer>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              {([[regionName(a), COLOR_A], [regionName(b), COLOR_B]] as const).map(([name, color]) => (
                <span key={name} className="inline-flex items-center gap-1.5">
                  <span className="inline-block w-5 border-t-2" style={{ borderColor: color }} />
                  {name}
                  <span className="ml-1 inline-block w-5 border-t-[3px] border-dashed" style={{ borderColor: color }} />
                  {t("trendLine")}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-2">
              {opposite ? <ArrowLeftRightIcon className="size-4" /> : <EqualIcon className="size-4" />}
              <Badge variant={opposite ? "default" : "secondary"}>
                {opposite ? t("oppositeBadge") : t("sameBadge")}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {compareSummary(data.result_a, data.result_b, a, b, variable, data.comparison.summary).map((line) => (
              <p key={line} className="leading-relaxed text-muted-foreground">{line}</p>
            ))}
            <div className="space-y-1.5 rounded-lg bg-muted/60 p-3">
              <p className="font-semibold">{t("compareWhy")}</p>
              <p className="leading-relaxed text-muted-foreground">{t("compareWhyText")}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Karşılaştır sekmesi: ölçüm + iki bölge seçimi, altında karşılaştırma görünümü.
// Açılışta yarışmanın kilit örneği seçili gelir: Konya ile Doğu Karadeniz'in yağışı.
export function CompareTab({ meta }: { meta: Meta }) {
  const ids = meta.regions.map((r) => r.id)
  const [variableId, setVariableId] = useState(meta.variables[0].id)
  const [regionA, setRegionA] = useState(ids[0])
  const [regionB, setRegionB] = useState(ids.includes("black_sea") ? "black_sea" : ids[ids.length - 1])
  const variable = meta.variables.find((v) => v.id === variableId)!
  const regionOptions = (other: string) =>
    meta.regions.map((r) => ({ id: r.id, name: regionName(r), disabled: r.id === other }))

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">{t("compareIntro")}</p>
      <Card size="sm">
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <Picker
            label={t("variable")}
            value={variableId}
            onChange={setVariableId}
            options={meta.variables.map((v) => ({ id: v.id, name: variableName(v) }))}
            hint={variableShort(variable)}
          />
          <Picker label={t("regionA")} value={regionA} onChange={setRegionA} options={regionOptions(regionB)} />
          <Picker label={t("regionB")} value={regionB} onChange={setRegionB} options={regionOptions(regionA)} />
        </CardContent>
      </Card>
      <CompareView meta={meta} variableId={variableId} regionA={regionA} regionB={regionB} />
    </div>
  )
}
