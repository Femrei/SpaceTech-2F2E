import type { ReactNode } from "react"
import { CircleCheckIcon, CircleDashedIcon } from "lucide-react"

import { InfoTip } from "@/components/InfoTip"
import { Card, CardContent } from "@/components/ui/card"
import type { TrendResult, Variable } from "@/lib/api"
import { trendKind, variableUnit } from "@/lib/content"
import { fmt, fmtP, fmtPct, t } from "@/lib/i18n"
import { TREND_ICON, TREND_TEXT, trendText } from "@/lib/trendStyle"

// Tek bir KPI kutusu: küçük başlık + (i) açıklaması, büyük değer (sayıysa mono), altında
// değeri sade dille anlatan kısa not.
function Tile({ label, help, value, caption, numeric = false }: {
  label: string
  help?: string
  value: ReactNode
  caption: ReactNode
  numeric?: boolean
}) {
  return (
    <Card size="sm" className="gap-1">
      <CardContent className="space-y-1">
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          {label}
          <InfoTip text={help} />
        </div>
        <div className={numeric ? "font-mono text-xl font-medium tracking-tight tabular-nums sm:text-2xl" : "text-xl font-semibold tracking-tight sm:text-2xl"}>{value}</div>
        <div className="text-xs text-muted-foreground">{caption}</div>
      </CardContent>
    </Card>
  )
}

// Panonun üstündeki 4 özet kutusu:
//   1) Genel gidişat (artıyor / azalıyor / belirgin değişim yok)
//   2) 10 yıldaki değişim (birimli, Sen eğimi: B'nin ana testiyle aynı yön)
//   3) Yüzde değişim (sıcaklık gibi sıfırı keyfi ölçümlerde gizlenir)
//   4) Gerçek mi? (istatistiksel anlamlılık + p-değeri)
export function KpiTiles({ result, variable, termHelp, showPercent = true }: {
  result: TrendResult
  variable: Variable
  termHelp: (term: string) => string | undefined
  showPercent?: boolean
}) {
  const kind = trendKind(result)
  const Icon = TREND_ICON[kind]
  const unit = variableUnit(variable)
  const pct = result.percent_change_per_decade

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Tile
        label={t("kpiDirection")}
        help={t("kpiDirectionHelp")}
        value={
          <span className="inline-flex items-center gap-1.5" style={{ color: TREND_TEXT[kind] }}>
            <Icon className="size-6 shrink-0" />
            <span className="text-xl leading-tight">{trendText(kind)}</span>
          </span>
        }
        caption={`${result.start_year}–${result.end_year}`}
      />
      <Tile
        label={t("kpiChange")}
        help={termHelp("per decade")}
        numeric
        value={
          <>
            {fmt(result.sen_slope_per_decade, 2, true)}
            <span className="ml-1.5 font-sans text-sm font-normal text-muted-foreground">{unit}</span>
          </>
        }
        caption={t("kpiChangeCaption")}
      />
      <Tile
        label={t("kpiPercent")}
        numeric
        value={!showPercent || pct === null ? "—" : fmtPct(pct)}
        caption={showPercent ? t("kpiPercentCaption") : t("noPercentCaption")}
      />
      <Tile
        label={t("kpiReliability")}
        help={termHelp("statistically significant")}
        value={
          <span className="inline-flex items-center gap-1.5">
            {result.significant ? (
              <CircleCheckIcon className="size-6 shrink-0 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <CircleDashedIcon className="size-6 shrink-0 text-muted-foreground" />
            )}
            <span className="text-xl leading-tight">
              {result.significant ? t("significant") : t("notSignificant")}
            </span>
          </span>
        }
        caption={`${fmtP(result.mk_p)} · ${result.significant ? t("sigCaption") : t("notSigCaption")}`}
      />
    </div>
  )
}
