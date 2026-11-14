import { useState, type ReactNode } from "react"
import { ChevronDownIcon, LightbulbIcon } from "lucide-react"

import type { ChartView } from "@/components/TrendChart"
import { InfoTip } from "@/components/InfoTip"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import type { Region, TrendResult, Variable } from "@/lib/api"
import { explain, trendKind, variableName, variableUnit } from "@/lib/content"
import { fmt, t } from "@/lib/i18n"
import { TREND_COLOR, TREND_ICON, trendText } from "@/lib/trendStyle"
import { cn } from "@/lib/utils"

// İstatistik detaylarındaki tek satır: terim adı + (i) açıklaması solda, değer sağda.
function StatRow({ label, help, value, note }: {
  label: string
  help?: string
  value: ReactNode
  note?: ReactNode
}) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5">
      <span className="inline-flex items-center gap-1 text-muted-foreground">
        {label}
        <InfoTip text={help} />
      </span>
      <span className="text-right">
        <span className="font-medium tabular-nums">{value}</span>
        {note && <span className="block text-xs text-muted-foreground">{note}</span>}
      </span>
    </div>
  )
}

// Panonun sağındaki açıklama kartı:
//   1) "Bu ne demek?": sonucu sade dille anlatan cümleler
//   2) "Grafik nasıl okunur?": seçili grafik görünümüne göre kısa rehber
//   3) Açılır "İstatistik detayları": OLS eğimi + aralığı, p-değeri, Sen eğimi, yıl sayısı
export function ExplainCard({ result, variable, region, interpretation, view, termHelp }: {
  result: TrendResult
  variable: Variable
  region: Region
  interpretation: string
  view: ChartView
  termHelp: (term: string) => string | undefined
}) {
  const [open, setOpen] = useState(false)
  const kind = trendKind(result)
  const Icon = TREND_ICON[kind]
  const unit = variableUnit(variable)
  const perDecade = t("perDecadeUnit", { unit })
  const howTo = view === "simple"
    ? [t("readSimple1"), t("readSimple2"), t("readSimple3"), t("readColors")]
    : [t("readDetailed1"), t("readDetailed2"), t("readColors")]

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <LightbulbIcon className="size-4 text-amber-500" />
          {t("whatItMeans")}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 text-sm">
        <div className="space-y-2">
          <p className="inline-flex items-center gap-1.5 font-semibold" style={{ color: TREND_COLOR[kind] }}>
            <Icon className="size-4" />
            {variableName(variable)}: {trendText(kind).toLocaleLowerCase()}
          </p>
          {explain(result, variable, region, interpretation).map((line) => (
            <p key={line} className="leading-relaxed text-muted-foreground">{line}</p>
          ))}
        </div>

        <div className="space-y-2">
          <p className="font-semibold">{t("howToRead")}</p>
          <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
            {howTo.map((line) => <li key={line}>{line}</li>)}
          </ul>
        </div>

        <Collapsible open={open} onOpenChange={setOpen} className="rounded-lg border">
          <CollapsibleTrigger className="flex w-full items-center justify-between px-3 py-2.5 font-medium">
            {t("statsDetails")}
            <ChevronDownIcon className={cn("size-4 transition-transform", open && "rotate-180")} />
          </CollapsibleTrigger>
          <CollapsibleContent className="divide-y border-t px-3">
            <StatRow
              label={t("olsSlope")}
              help={termHelp("trend")}
              value={`${fmt(result.slope_per_decade, 3, true)} ${perDecade}`}
              note={t("ciRange", { low: fmt(result.ci_low, 3, true), high: fmt(result.ci_high, 3, true) })}
            />
            <StatRow label={t("mkP")} help={termHelp("p-value")} value={fmt(result.mk_p, 4)} />
            <StatRow
              label={t("senSlope")}
              help={termHelp("Sen's slope")}
              value={`${fmt(result.sen_slope_per_decade, 3, true)} ${perDecade}`}
            />
            <StatRow label={t("yearsOfData")} help={termHelp("area-averaged")} value={result.n_years} />
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
