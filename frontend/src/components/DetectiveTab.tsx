import { useState } from "react"
import {
  ArrowLeftIcon,
  ArrowRightIcon,
  DropletsIcon,
  RotateCcwIcon,
  ScaleIcon,
  SearchIcon,
  SunIcon,
  ThermometerSunIcon,
} from "lucide-react"

import { AnalysisBlock } from "@/components/AnalysisBlock"
import { CompareView } from "@/components/CompareTab"
import { LoadingPanels, Warning } from "@/components/Common"
import { RegionMap } from "@/components/RegionMap"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { fetchSuggestions, type Analysis, type Meta, type Suggestion } from "@/lib/api"
import {
  hintText,
  reasonText,
  regionName,
  themeBlurb,
  themeLabel,
  variableName,
} from "@/lib/content"
import { t } from "@/lib/i18n"
import { scrollBehavior } from "@/lib/motion"
import { cn } from "@/lib/utils"

const THEME_ICONS: Record<string, typeof SunIcon> = {
  drought: SunIcon,
  warming: ThermometerSunIcon,
  water: DropletsIcon,
}

type Step = { regionId: string; variableId: string }

// Üstteki adım göstergesi: 1 Soru seç · 2 Nereden başlayalım? · 3 İncele.
// Geçilmiş adımlara tıklayınca o adıma geri dönülür.
function Stepper({ current, onGo }: { current: 1 | 2 | 3; onGo: (step: 1 | 2) => void }) {
  const steps = [t("detStep1"), t("detStep2"), t("detStep3")]
  return (
    <ol className="flex flex-wrap items-center gap-2 text-sm">
      {steps.map((label, i) => {
        const n = (i + 1) as 1 | 2 | 3
        const done = n < current
        return (
          <li key={label} className="flex items-center gap-2">
            {i > 0 && <span className="h-px w-4 bg-border sm:w-8" />}
            <button
              type="button"
              disabled={!done}
              onClick={() => done && onGo(n as 1 | 2)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full px-1 py-0.5",
                done && "hover:underline",
                n === current ? "font-semibold" : "text-muted-foreground",
              )}
            >
              <span
                className={cn(
                  "flex size-6 items-center justify-center rounded-full border text-xs",
                  n === current && "border-primary bg-primary text-primary-foreground",
                  done && "border-primary text-primary",
                )}
              >
                {n}
              </span>
              {label}
            </button>
          </li>
        )
      })}
    </ol>
  )
}

// Dedektif Modu sekmesi. Adımlar arası geçiş bu bileşenin durumunda (state) tutulur:
//   1) Tema seç: "Kuruyor mu?", "Isınıyor mu?", "Suya ne oluyor?"
//   2) D'nin suggest() önerileri: her biri gerekçesiyle, en iyisi ilk sırada
//   3) İnceleme: dedektifin ipucu + harita, altında tam analiz. "İpucunu takip et"
//      aynı bölgede bir sonraki değişkene geçer; izlenen yol üstte listelenir.
export function DetectiveTab({ meta }: { meta: Meta }) {
  const [theme, setTheme] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[] | null>(null)
  const [suggestError, setSuggestError] = useState(false)
  const [trail, setTrail] = useState<Step[]>([])
  const [compareWith, setCompareWith] = useState<string | null>(null)

  const current = trail.at(-1)
  const stepNo: 1 | 2 | 3 = !theme ? 1 : !current ? 2 : 3

  // Tema seçilince önerileri backend'den çeker ve 2. adıma geçer.
  const pickTheme = (key: string) => {
    setTheme(key)
    setSuggestions(null)
    setSuggestError(false)
    setTrail([])
    setCompareWith(null)
    fetchSuggestions(key).then(setSuggestions).catch(() => setSuggestError(true))
  }

  // Adım göstergesinden geri dönüş: 1 -> her şeyi sıfırla, 2 -> önerilere dön.
  const goTo = (step: 1 | 2) => {
    setTrail([])
    setCompareWith(null)
    if (step === 1) setTheme(null)
  }

  // Yeni bir bölge + değişken incelemeye başlar (izlenen yola ekler).
  const investigate = (s: Step) => {
    setCompareWith(null)
    setTrail((prev) => [...prev, s])
    window.scrollTo({ top: 0, behavior: scrollBehavior() })
  }

  // İpucu kartı: dedektifin notu (D'nin next_step kuralı), sonraki adım butonları
  // ve küçük harita. İpucu aynı bölgede başka bir ölçüme ya da başka bir bölgeye
  // (karşılaştırma bölgesine) yönlendirebilir.
  const clueCard = (analysis: Analysis) => {
    if (!current) return null
    const region = meta.regions.find((r) => r.id === current.regionId)!
    const compare = meta.regions.find((r) => r.id === region.compare_with)
    const text = hintText(meta.hints, analysis.result, current.variableId, region, compare, analysis.next_step.text)

    // Takip edilecek hedef. Daha önce incelenmişse döngüye girmemek için bu bölgede
    // henüz bakılmamış ilk ölçüme yönlendir; hepsine bakıldıysa karşılaştırma öner.
    const { variable_id: nextVar, region_id: nextRegion } = analysis.next_step
    let target: Step | null = nextVar && nextRegion ? { regionId: nextRegion, variableId: nextVar } : null
    let note: string | null = null
    const seen = (s: Step) => trail.some((x) => x.regionId === s.regionId && x.variableId === s.variableId)
    if (target && seen(target)) {
      const already = meta.variables.find((v) => v.id === target!.variableId)!
      const visitedHere = new Set(trail.filter((s) => s.regionId === current.regionId).map((s) => s.variableId))
      const fresh = meta.variables.find((v) => !visitedHere.has(v.id))
      target = fresh ? { regionId: current.regionId, variableId: fresh.id } : null
      note = fresh
        ? t("alreadyVisited", { done: variableName(already), next: variableName(fresh) })
        : t("allVisited")
    }
    const targetRegion = target ? meta.regions.find((r) => r.id === target!.regionId) : undefined
    const targetVariable = target ? meta.variables.find((v) => v.id === target!.variableId) : undefined
    const otherRegion = target && target.regionId !== current.regionId ? targetRegion : compare
    return (
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="border-primary/40 lg:col-span-2">
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <SearchIcon className="size-4" />
              {t("clueTitle")}
            </div>
            <p className="text-base leading-relaxed">{text}</p>
            {note && <p className="text-sm text-muted-foreground">{note}</p>}
            <div className="flex flex-wrap gap-2">
              {target && targetVariable && targetRegion && (
                <Button onClick={() => investigate(target!)}>
                  {t("followClue")}: {variableName(targetVariable)}
                  {target.regionId !== current.regionId && ` · ${regionName(targetRegion)}`}
                  <ArrowRightIcon />
                </Button>
              )}
              {otherRegion && (
                <Button variant={target ? "outline" : "default"} onClick={() => setCompareWith(otherRegion.id)}>
                  <ScaleIcon />
                  {t("openCompare")}: {regionName(otherRegion)}
                </Button>
              )}
              <Button variant="outline" onClick={() => goTo(2)}>
                <ArrowLeftIcon />
                {t("backToSuggestions")}
              </Button>
              <Button variant="ghost" onClick={() => goTo(1)}>
                <RotateCcwIcon />
                {t("startOver")}
              </Button>
            </div>
          </CardContent>
        </Card>
        <RegionMap regions={meta.regions} selectedId={current.regionId} />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">{t("detIntro")}</p>
      <Stepper current={stepNo} onGo={goTo} />

      {stepNo === 1 && (
        <div className="grid gap-3 sm:grid-cols-3">
          {Object.entries(meta.themes).map(([key, label]) => {
            const Icon = THEME_ICONS[key] ?? SearchIcon
            return (
              <button
                key={key}
                type="button"
                onClick={() => pickTheme(key)}
                className="group rounded-xl border bg-card p-5 text-left transition-colors hover:border-primary hover:bg-muted/50"
              >
                <Icon className="mb-3 size-7 text-primary" />
                <div className="text-lg font-semibold">{themeLabel(key, label)}</div>
                <p className="mt-1 text-sm text-muted-foreground">{themeBlurb(key)}</p>
              </button>
            )
          })}
        </div>
      )}

      {stepNo === 2 && (
        suggestError ? (
          <Warning>{t("loadError")}</Warning>
        ) : !suggestions ? (
          <LoadingPanels />
        ) : (
          <div className="space-y-3">
            <h2 className="font-heading text-xl font-semibold">{themeLabel(theme!, meta.themes[theme!])}</h2>
            <div className="grid gap-3 md:grid-cols-2">
              {suggestions.map((s, i) => {
                const region = meta.regions.find((r) => r.id === s.region_id)
                const variable = meta.variables.find((v) => v.id === s.variable_id)
                if (!region || !variable) return null
                return (
                  <Card key={`${s.region_id}/${s.variable_id}`} size="sm" className={cn(i === 0 && "border-primary/50")}>
                    <CardContent className="flex h-full flex-col gap-3">
                      <div className="space-y-1">
                        {i === 0 && <Badge>{t("bestPick")}</Badge>}
                        <div className="font-semibold">
                          {variableName(variable)} · {regionName(region)}
                        </div>
                        <p className="text-sm text-muted-foreground">{reasonText(theme!, s.variable_id, region, s.reason)}</p>
                      </div>
                      <Button
                        className="mt-auto self-start"
                        variant={i === 0 ? "default" : "outline"}
                        onClick={() => investigate({ regionId: s.region_id, variableId: s.variable_id })}
                      >
                        <SearchIcon />
                        {t("investigate")}
                      </Button>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          </div>
        )
      )}

      {stepNo === 3 && current && (
        <div className="space-y-4">
          {trail.length > 1 && (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-muted-foreground">{t("trail")}:</span>
              {trail.map((s, i) => (
                <span key={i} className="inline-flex items-center gap-2">
                  {i > 0 && <ArrowRightIcon className="size-3.5 text-muted-foreground" />}
                  <Badge variant={i === trail.length - 1 ? "default" : "secondary"}>
                    {variableName(meta.variables.find((v) => v.id === s.variableId)!)}
                  </Badge>
                </span>
              ))}
            </div>
          )}

          {compareWith ? (
            <div className="space-y-4">
              <Button variant="outline" onClick={() => setCompareWith(null)}>
                <ArrowLeftIcon />
                {regionName(meta.regions.find((r) => r.id === current.regionId)!)} ·{" "}
                {variableName(meta.variables.find((v) => v.id === current.variableId)!)}
              </Button>
              <CompareView meta={meta} variableId={current.variableId} regionA={current.regionId} regionB={compareWith} />
            </div>
          ) : (
            <AnalysisBlock
              key={`${current.regionId}/${current.variableId}/${trail.length}`}
              meta={meta}
              regionId={current.regionId}
              variableId={current.variableId}
              extra={clueCard}
            />
          )}
        </div>
      )}
    </div>
  )
}
