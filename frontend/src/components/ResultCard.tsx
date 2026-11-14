import { useState, type ReactNode } from "react"
import { ChevronDownIcon, CircleCheckIcon, CircleIcon } from "lucide-react"

import { InfoTip } from "@/components/InfoTip"
import { Card, CardContent } from "@/components/ui/card"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import type { TrendResult, Variable } from "@/lib/api"
import { fmt, t } from "@/lib/i18n"
import { cn } from "@/lib/utils"

// Tek bir istatistik kutusu: üstte başlık + (i) açıklaması, ortada büyük değer,
// altta isteğe bağlı küçük not (ör. p-değeri).
function Stat({ label, help, value, note, className }: {
  label: string
  help?: string
  value: ReactNode
  note?: ReactNode
  className?: string
}) {
  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center gap-1 text-sm text-muted-foreground">
        {label}
        <InfoTip text={help} />
      </div>
      <div className="text-2xl font-semibold tracking-tight break-words">{value}</div>
      {note && <div className="text-xs text-muted-foreground">{note}</div>}
    </div>
  )
}

// Sonuç kartını çizer:
//   1) 3 kutu: 10 yıllık değişim (birimli), % değişim, anlamlılık (+ p-değeri)
//   2) B'nin interpret() fonksiyonundan gelen açıklama metni
//   3) Açılır "İstatistik detayları": OLS eğimi + güven aralığı, Mann-Kendall p,
//      Sen eğimi, yıl sayısı
export function ResultCard({ result, variable, interpretation, termHelp }: {
  result: TrendResult
  variable: Variable
  interpretation: string
  termHelp: (term: string) => string | undefined
}) {
  const [open, setOpen] = useState(false)
  const unit = variable.unit
  const perDecade = t("perDecadeUnit", { unit })
  const pct = result.percent_change_per_decade

  return (
    <Card>
      <CardContent className="space-y-5">
        <div className="grid gap-5 sm:grid-cols-3">
          <Stat
            label={t("changePerDecade")}
            help={termHelp("per decade")}
            value={`${fmt(result.slope_per_decade, 2, true)} ${unit}`}
          />
          <Stat
            label={t("pctPerDecade")}
            help={t("pctHelp")}
            value={pct === null ? t("notAvailable") : `${fmt(pct, 1, true)}%`}
          />
          <Stat
            label={t("significance")}
            help={termHelp("statistically significant")}
            value={
              <span className="inline-flex items-center gap-2">
                {result.significant ? (
                  <CircleCheckIcon className="size-6 text-emerald-600 dark:text-emerald-400" />
                ) : (
                  <CircleIcon className="size-6 text-muted-foreground" />
                )}
                {result.significant ? t("significant") : t("notSignificant")}
              </span>
            }
            note={`Mann-Kendall p = ${fmt(result.mk_p, 3)}`}
          />
        </div>

        <blockquote className="border-l-2 pl-4 text-sm leading-relaxed text-muted-foreground">
          {interpretation}
        </blockquote>

        <Collapsible open={open} onOpenChange={setOpen} className="rounded-lg border">
          <CollapsibleTrigger className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium">
            📊 {t("statsDetails")}
            <ChevronDownIcon className={cn("size-4 transition-transform", open && "rotate-180")} />
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4 border-t px-4 py-4">
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <Stat
                className="[&>div:nth-child(2)]:text-lg"
                label={t("olsSlope")}
                help={termHelp("trend")}
                value={`${fmt(result.slope_per_decade, 3, true)} ${perDecade}`}
                note={
                  <span className="inline-flex items-center gap-1">
                    {t("ciRange", { low: fmt(result.ci_low, 3, true), high: fmt(result.ci_high, 3, true) })}
                    <InfoTip text={termHelp("confidence interval")} />
                  </span>
                }
              />
              <Stat
                className="[&>div:nth-child(2)]:text-lg"
                label={t("mkP")}
                help={termHelp("Mann-Kendall test") ?? termHelp("p-value")}
                value={fmt(result.mk_p, 4)}
              />
              <Stat
                className="[&>div:nth-child(2)]:text-lg"
                label={t("senSlope")}
                help={termHelp("Sen's slope")}
                value={`${fmt(result.sen_slope_per_decade, 3, true)} ${perDecade}`}
              />
              <Stat
                className="[&>div:nth-child(2)]:text-lg"
                label={t("yearsOfData")}
                help={termHelp("area-averaged")}
                value={result.n_years}
              />
            </div>
            <p className="text-xs text-muted-foreground">{t("anomalyNote")}</p>
          </CollapsibleContent>
        </Collapsible>
      </CardContent>
    </Card>
  )
}
