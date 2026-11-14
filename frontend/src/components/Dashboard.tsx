import { useEffect, useRef, useState, type ReactNode } from "react"
import { TriangleAlertIcon } from "lucide-react"

import { ExplainCard } from "@/components/ExplainCard"
import { KpiTiles } from "@/components/KpiTiles"
import { OverviewGrid } from "@/components/OverviewGrid"
import { TrendChart, type ChartView } from "@/components/TrendChart"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  ApiError,
  fetchAnalysis,
  fetchOverview,
  type Analysis,
  type Meta,
  type OverviewItem,
} from "@/lib/api"
import {
  makeTermHelp,
  regionDescription,
  regionName,
  variableName,
  variableShort,
  variableUnit,
} from "@/lib/content"
import { t } from "@/lib/i18n"

// Kullanıcıya sarı uyarı kutusu gösterir (veri yok, yetersiz veri vb.).
function Warning({ children }: { children: ReactNode }) {
  return (
    <Alert>
      <TriangleAlertIcon />
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  )
}

// Etiketli açılır seçim kutusu + altında seçili öğenin kısa açıklaması.
// Listede isim görünür, arka planda id kullanılır.
function Picker({ label, value, onChange, options, hint }: {
  label: string
  value: string
  onChange: (id: string) => void
  options: { id: string; name: string }[]
  hint: string
}) {
  return (
    <div className="grid content-start gap-1.5">
      <label className="text-sm font-medium">{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full" aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.id} value={o.id}>
              {o.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-xs leading-relaxed text-muted-foreground">{hint}</p>
    </div>
  )
}

// Pano (dashboard) sekmesinin tamamı, yukarıdan aşağıya:
//   1) Bölge + ölçüm seçimi (her birinin kısa açıklamasıyla)
//   2) 4 özet kutusu (KPI)
//   3) Solda grafik (Basit / Detaylı), sağda "Bu ne demek?" açıklama kartı
//   4) Tüm bölgeler bir bakışta: tıklanabilir 3x3 özet ızgarası
// Seçim değişince backend'den analizi çeker; beklerken iskelet (skeleton) gösterir.
export function Dashboard({ meta }: { meta: Meta }) {
  const [regionId, setRegionId] = useState(meta.regions[0].id)
  const [variableId, setVariableId] = useState(meta.variables[0].id)
  const [view, setView] = useState<ChartView>("simple")
  const [analysis, setAnalysis] = useState<{ key: string; data: Analysis } | null>(null)
  const [error, setError] = useState<{ key: string; message: string } | null>(null)
  const [overview, setOverview] = useState<OverviewItem[] | null>(null)
  const topRef = useRef<HTMLDivElement>(null)

  const key = `${regionId}/${variableId}`
  const region = meta.regions.find((r) => r.id === regionId)!
  const variable = meta.variables.find((v) => v.id === variableId)!
  const unit = variableUnit(variable)
  const hasData = meta.pairs.some(([r, v]) => r === regionId && v === variableId)
  const termHelp = makeTermHelp(meta.glossary)
  const current = analysis?.key === key ? analysis.data : null
  const currentError = error?.key === key ? error.message : null

  // Genel bakış ızgarasının verisini açılışta bir kez çeker.
  useEffect(() => {
    fetchOverview().then(setOverview).catch(() => setOverview([]))
  }, [])

  // Seçim değişince analizi çeker. Sonuç hangi seçime aitse o anahtarla saklanır;
  // böylece geç gelen eski bir cevap yeni seçimin yerine gösterilmez.
  useEffect(() => {
    if (!hasData) return
    fetchAnalysis(regionId, variableId)
      .then((data) => setAnalysis({ key: `${regionId}/${variableId}`, data }))
      .catch((e: unknown) =>
        setError({
          key: `${regionId}/${variableId}`,
          message: e instanceof ApiError && e.status === 422 ? `${t("notEnoughData")} ${e.message}` : t("loadError"),
        }),
      )
  }, [regionId, variableId, hasData])

  // Izgaradan bir kutu seçilince o bölge + ölçümü açar ve panonun başına kaydırır.
  const selectFromGrid = (r: string, v: string) => {
    setRegionId(r)
    setVariableId(v)
    topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  return (
    <div className="space-y-5">
      <div ref={topRef} className="scroll-mt-20" />
      <p className="text-sm text-muted-foreground">{t("intro")}</p>

      <Card size="sm">
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <Picker
            label={t("region")}
            value={regionId}
            onChange={setRegionId}
            options={meta.regions.map((r) => ({ id: r.id, name: regionName(r) }))}
            hint={regionDescription(region)}
          />
          <Picker
            label={t("variable")}
            value={variableId}
            onChange={setVariableId}
            options={meta.variables.map((v) => ({ id: v.id, name: variableName(v) }))}
            hint={variableShort(variable)}
          />
        </CardContent>
      </Card>

      {!hasData ? (
        <Warning>{t("noData", { variable: variableName(variable), region: regionName(region) })}</Warning>
      ) : currentError ? (
        <Warning>{currentError}</Warning>
      ) : !current ? (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-[420px] w-full" />
        </div>
      ) : (
        <>
          <KpiTiles result={current.result} variable={variable} termHelp={termHelp} />

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>
                  {regionName(region)} · {variableName(variable)}
                </CardTitle>
                <CardDescription>{t("sourceCaption", { dataset: variable.dataset })}</CardDescription>
                <CardAction>
                  <Tabs value={view} onValueChange={(v) => setView(v as ChartView)}>
                    <TabsList>
                      <TabsTrigger value="simple">{t("viewSimple")}</TabsTrigger>
                      <TabsTrigger value="detailed">{t("viewDetailed")}</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </CardAction>
              </CardHeader>
              <CardContent>
                <TrendChart points={current.points} result={current.result} unit={unit} view={view} />
              </CardContent>
            </Card>
            <ExplainCard
              result={current.result}
              variable={variable}
              region={region}
              interpretation={current.interpretation}
              view={view}
              termHelp={termHelp}
            />
          </div>
        </>
      )}

      {overview && overview.length > 0 && (
        <OverviewGrid
          meta={meta}
          items={overview}
          regionId={regionId}
          variableId={variableId}
          onSelect={selectFromGrid}
        />
      )}
    </div>
  )
}
