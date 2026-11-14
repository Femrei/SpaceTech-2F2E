import { useEffect, useState, type ReactNode } from "react"
import { TriangleAlertIcon } from "lucide-react"

import { makeTermHelp } from "@/components/InfoTip"
import { ResultCard } from "@/components/ResultCard"
import { TrendChart } from "@/components/TrendChart"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { ApiError, fetchAnalysis, type Analysis, type Meta } from "@/lib/api"
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

// Etiketli açılır seçim kutusu: listede isim görünür, arka planda id kullanılır.
function Picker({ label, value, onChange, options }: {
  label: string
  value: string
  onChange: (id: string) => void
  options: { id: string; name: string }[]
}) {
  return (
    <label className="grid gap-1.5 text-sm font-medium">
      {label}
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full">
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
    </label>
  )
}

// Explore sekmesinin tamamı:
// bölge/değişken seçimi -> değişken açıklaması -> grafik -> sonuç kartı.
// Seçim değişince backend'den analizi çeker; beklerken iskelet (skeleton) gösterir,
// veri yoksa ya da yetersizse (24 aydan az) uyarı gösterir.
export function ExploreTab({ meta }: { meta: Meta }) {
  const [regionId, setRegionId] = useState(meta.regions[0].id)
  const [variableId, setVariableId] = useState(meta.variables[0].id)
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [error, setError] = useState<string | null>(null)

  const region = meta.regions.find((r) => r.id === regionId)!
  const variable = meta.variables.find((v) => v.id === variableId)!
  const hasData = meta.pairs.some(([r, v]) => r === regionId && v === variableId)
  const termHelp = makeTermHelp(meta.glossary)

  // Seçim değişince analizi yeniden çeker. Eski isteğin cevabı geç gelirse
  // ("ignore" bayrağı sayesinde) yeni seçimin üzerine yazılmaz.
  useEffect(() => {
    if (!hasData) return
    let ignore = false
    setAnalysis(null)
    setError(null)
    fetchAnalysis(regionId, variableId)
      .then((a) => !ignore && setAnalysis(a))
      .catch((e: unknown) => {
        if (ignore) return
        setError(e instanceof ApiError && e.status === 422 ? `${t("notEnoughData")} ${e.message}` : t("loadError"))
      })
    return () => {
      ignore = true
    }
  }, [regionId, variableId, hasData])

  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Picker label={t("region")} value={regionId} onChange={setRegionId} options={meta.regions} />
        <Picker label={t("variable")} value={variableId} onChange={setVariableId} options={meta.variables} />
      </div>

      <p className="text-sm text-muted-foreground">
        <span className="font-medium text-foreground">{variable.name}:</span> {variable.short_description}
      </p>

      {!hasData ? (
        <Warning>{t("noData", { variable: variable.name, region: region.name })}</Warning>
      ) : error ? (
        <Warning>{error}</Warning>
      ) : !analysis ? (
        <div className="space-y-3">
          <Skeleton className="h-[480px] w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : (
        <>
          <Card>
            <CardContent className="space-y-2">
              <TrendChart points={analysis.points} result={analysis.result} variable={variable} region={region} />
              <p className="pt-2 text-xs text-muted-foreground">
                {t("sourceCaption", { dataset: variable.dataset, unit: variable.unit, region: region.name })}
              </p>
            </CardContent>
          </Card>
          <ResultCard
            result={analysis.result}
            variable={variable}
            interpretation={analysis.interpretation}
            termHelp={termHelp}
          />
        </>
      )}
    </div>
  )
}
