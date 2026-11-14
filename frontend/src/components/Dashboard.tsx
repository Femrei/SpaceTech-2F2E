import { useEffect, useRef, useState } from "react"

import { AnalysisBlock } from "@/components/AnalysisBlock"
import { Picker } from "@/components/Common"
import { OverviewGrid } from "@/components/OverviewGrid"
import { RegionMap } from "@/components/RegionMap"
import { Card, CardContent } from "@/components/ui/card"
import { fetchOverview, type Meta, type OverviewItem } from "@/lib/api"
import { regionDescription, regionName, variableName, variableShort } from "@/lib/content"
import { t } from "@/lib/i18n"

// Pano (dashboard) sekmesinin tamamı, yukarıdan aşağıya:
//   1) Bölge + ölçüm seçimi (kısa açıklamalarıyla), altında geniş bölge haritası
//   2) Analiz bloğu: 4 özet kutusu, grafik (Basit/Detaylı), "Bu ne demek?" kartı
//   3) Tüm bölgeler bir bakışta: tıklanabilir 3x3 özet ızgarası
export function Dashboard({ meta }: { meta: Meta }) {
  const [regionId, setRegionId] = useState(meta.regions[0].id)
  const [variableId, setVariableId] = useState(meta.variables[0].id)
  const [overview, setOverview] = useState<OverviewItem[] | null>(null)
  const topRef = useRef<HTMLDivElement>(null)

  const region = meta.regions.find((r) => r.id === regionId)!
  const variable = meta.variables.find((v) => v.id === variableId)!

  // Genel bakış ızgarasının verisini açılışta bir kez çeker.
  useEffect(() => {
    fetchOverview().then(setOverview).catch(() => setOverview([]))
  }, [])

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
        <CardContent className="space-y-4">
          <div className="grid content-start gap-4 sm:grid-cols-2">
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
          </div>
          <RegionMap
            regions={meta.regions}
            selectedId={regionId}
            onSelect={setRegionId}
            mapClassName="h-72 sm:h-96"
          />
        </CardContent>
      </Card>

      <AnalysisBlock meta={meta} regionId={regionId} variableId={variableId} />

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
