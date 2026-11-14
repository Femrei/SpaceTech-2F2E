import { useState } from "react"
import { ArrowLeftIcon, ArrowRightIcon, FolderOpenIcon, ScaleIcon } from "lucide-react"

import { AnalysisBlock } from "@/components/AnalysisBlock"
import { CompareView } from "@/components/CompareTab"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import type { Case, Meta } from "@/lib/api"
import { caseStory, caseTitle, regionName, variableName } from "@/lib/content"
import { t } from "@/lib/i18n"
import { scrollBehavior } from "@/lib/motion"

// Vaka kartındaki küçük etiketler: hangi bölge(ler) ve hangi ölçüm.
function CaseTags({ meta, c }: { meta: Meta; c: Case }) {
  const region = meta.regions.find((r) => r.id === c.region_id)
  const other = meta.regions.find((r) => r.id === c.compare_region_id)
  const variable = meta.variables.find((v) => v.id === c.variable_id)
  return (
    <div className="flex flex-wrap gap-1.5">
      {variable && <Badge variant="secondary">{variableName(variable)}</Badge>}
      {region && <Badge variant="outline">{regionName(region)}</Badge>}
      {other && <Badge variant="outline">{regionName(other)}</Badge>}
      {other && (
        <Badge>
          <ScaleIcon />
          {t("compareCase")}
        </Badge>
      )}
    </div>
  )
}

// Zincirli vakada (ör. Vaka 4: yağış -> sıcaklık -> toprak nemi) şüphelileri sırayla
// gösteren adım düğmeleri. Seçili adım vurgulanır; her biri o ölçümün analizini açar.
function ChainSteps({ meta, chain, step, onStep }: {
  meta: Meta
  chain: string[]
  step: number
  onStep: (i: number) => void
}) {
  return (
    <nav aria-label={t("chainLabel")} className="flex flex-wrap items-center gap-2 text-sm">
      <span className="text-muted-foreground">{t("chainLabel")}:</span>
      {chain.map((id, i) => {
        const variable = meta.variables.find((v) => v.id === id)
        if (!variable) return null
        return (
          <span key={id} className="inline-flex items-center gap-2">
            {i > 0 && <ArrowRightIcon className="size-3.5 text-muted-foreground" aria-hidden="true" />}
            <Button size="sm" variant={i === step ? "default" : "outline"} aria-current={i === step ? "step" : undefined} onClick={() => onStep(i)}>
              {i + 1}. {variableName(variable)}
            </Button>
          </span>
        )
      })}
    </nav>
  )
}

// Vaka Dosyaları sekmesi: D'nin get_cases() vakaları kart olarak listelenir
// (başlık + hikâye + "Vakayı aç"). Açılan vaka tek bölgeliyse tam analiz,
// compare_region_id doluysa iki bölgeli karşılaştırma görünümü gösterilir.
export function CasesTab({ meta }: { meta: Meta }) {
  const [openId, setOpenId] = useState<string | null>(null)
  const [step, setStep] = useState(0)
  const opened = meta.cases.find((c) => c.id === openId)

  // Bir vakayı açar (zincirli vakada ilk adımdan başlar) ve sayfanın başına kaydırır.
  const open = (id: string | null) => {
    setOpenId(id)
    setStep(0)
    window.scrollTo({ top: 0, behavior: scrollBehavior() })
  }

  if (opened) {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={() => open(null)}>
          <ArrowLeftIcon />
          {t("backToCases")}
        </Button>
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{caseTitle(opened)}</CardTitle>
            <CardDescription className="text-sm leading-relaxed">{caseStory(opened)}</CardDescription>
          </CardHeader>
          <CardContent>
            <CaseTags meta={meta} c={opened} />
          </CardContent>
        </Card>
        {opened.chain && opened.chain.length > 1 && (
          <ChainSteps meta={meta} chain={opened.chain} step={step} onStep={setStep} />
        )}
        {opened.compare_region_id ? (
          <CompareView
            meta={meta}
            variableId={opened.variable_id}
            regionA={opened.region_id}
            regionB={opened.compare_region_id}
          />
        ) : (
          <AnalysisBlock
            meta={meta}
            regionId={opened.region_id}
            variableId={opened.chain?.[step] ?? opened.variable_id}
          />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">{t("casesIntro")}</p>
      <div className="grid gap-4 md:grid-cols-2">
        {meta.cases.map((c) => (
          <Card key={c.id} className="flex flex-col">
            <CardHeader>
              <CardTitle className="flex items-start gap-2 text-base">
                <FolderOpenIcon className="mt-0.5 size-4 shrink-0 text-primary" />
                {caseTitle(c)}
              </CardTitle>
              <CardDescription className="leading-relaxed">{caseStory(c)}</CardDescription>
            </CardHeader>
            <CardContent>
              <CaseTags meta={meta} c={c} />
            </CardContent>
            <CardFooter className="mt-auto">
              <Button onClick={() => open(c.id)}>
                <FolderOpenIcon />
                {t("openCase")}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
