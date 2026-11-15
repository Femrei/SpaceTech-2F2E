import { useState, type ReactNode } from "react"

import { LoadingPanels, Warning } from "@/components/Common"
import { ExplainCard } from "@/components/ExplainCard"
import { KpiTiles } from "@/components/KpiTiles"
import { TrendChart, type ChartView } from "@/components/TrendChart"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Analysis, Meta, Region, Variable } from "@/lib/api"
import { makeTermHelp, regionName, variableName, variablePeriodNote, variableUnit } from "@/lib/content"
import { t } from "@/lib/i18n"
import { useAnalysis } from "@/lib/useAnalysis"

// Basit/Detaylı seçicisinde seçili seçenek iki temada da net ayrışsın
// ("Konumunu seç" sekmesindeki Nokta/Kare seçicisi de aynı görünümü kullanır).
export const SEGMENT = "px-3 data-active:bg-card data-active:shadow-sm dark:data-active:border-transparent dark:data-active:bg-white/15"

// Bir bölge + değişkenin tam analiz görünümü (Pano ve Dedektif Modu aynı bloğu kullanır):
//   4 özet kutusu -> solda grafik (Basit/Detaylı), sağda "Bu ne demek?" kartı.
// Veriyi kendisi çeker; beklerken iskelet, sorun varsa uyarı gösterir.
// "extra" verilirse analiz yüklendikten sonra özet kutularının üstünde gösterilir
// (ör. Dedektif Modu'ndaki ipucu kartı).
export function AnalysisBlock({ meta, regionId, variableId, extra }: {
  meta: Meta
  regionId: string
  variableId: string
  extra?: (analysis: Analysis) => ReactNode
}) {
  const region = meta.regions.find((r) => r.id === regionId)
  const variable = meta.variables.find((v) => v.id === variableId)
  const hasData = meta.pairs.some(([r, v]) => r === regionId && v === variableId)
  const state = useAnalysis(regionId, variableId, hasData)

  if (!region || !variable) return null
  if (!hasData) {
    return <Warning>{t("noData", { variable: variableName(variable), region: regionName(region) })}</Warning>
  }
  if (!state) return <LoadingPanels />
  if (state.error || !state.data) return <Warning>{state.error}</Warning>
  return <AnalysisPanels meta={meta} region={region} variable={variable} data={state.data} extra={extra} />
}

// Yüklenmiş bir analizin görünümü: 4 özet kutusu, grafik kartı (Basit/Detaylı) ve
// "Bu ne demek?" kartı. AnalysisBlock ve "Konumunu seç" sekmesi aynı görünümü kullanır.
// "region" katalogdaki bir bölge ya da haritada seçilen nokta için kurulmuş bir yer
// tanımıdır; "note" verilirse grafik kartının altına ek bir not olarak yazılır,
// "caption" verilirse grafik başlığının altındaki kaynak satırının yerine geçer.
export function AnalysisPanels({ meta, region, variable, data, extra, note, caption }: {
  meta: Meta
  region: Region
  variable: Variable
  data: Analysis
  extra?: (analysis: Analysis) => ReactNode
  note?: ReactNode
  caption?: string
}) {
  const [view, setView] = useState<ChartView>("simple")
  const termHelp = makeTermHelp(meta.glossary)
  const showPercent = !(meta.no_percent_variables ?? []).includes(variable.id)
  return (
    <div className="space-y-4">
      {extra?.(data)}
      <KpiTiles result={data.result} variable={variable} termHelp={termHelp} showPercent={showPercent} />
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              {regionName(region)} · {variableName(variable)}
            </CardTitle>
            <CardDescription>{caption ?? t("sourceCaption", { dataset: variable.dataset })}</CardDescription>
            <CardAction>
              <Tabs value={view} onValueChange={(v) => setView(v as ChartView)}>
                <TabsList>
                  <TabsTrigger value="simple" className={SEGMENT}>{t("viewSimple")}</TabsTrigger>
                  <TabsTrigger value="detailed" className={SEGMENT}>{t("viewDetailed")}</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardAction>
          </CardHeader>
          <CardContent>
            <TrendChart points={data.points} result={data.result} unit={variableUnit(variable)} view={view} />
            {variablePeriodNote(variable) && (
              <p className="mt-3 text-xs text-muted-foreground">
                {t("periodNote")}: {variablePeriodNote(variable)}
              </p>
            )}
            {note && <div className="mt-3 text-xs text-muted-foreground">{note}</div>}
          </CardContent>
        </Card>
        <ExplainCard
          result={data.result}
          variable={variable}
          region={region}
          interpretation={data.interpretation}
          view={view}
          termHelp={termHelp}
          showPercent={showPercent}
        />
      </div>
    </div>
  )
}
