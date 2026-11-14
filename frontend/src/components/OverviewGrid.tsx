import { Line, LineChart, ResponsiveContainer, YAxis } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { Meta, OverviewItem } from "@/lib/api"
import { regionName, trendKind, variableName, variableUnit } from "@/lib/content"
import { fmt, t } from "@/lib/i18n"
import { TREND_COLOR, TREND_ICON, TREND_TEXT, trendText } from "@/lib/trendStyle"
import { cn } from "@/lib/utils"

// Izgaradaki tek kutu: ölçüm adı, yön oku + yazısı, 10 yıllık değişim ve
// yıllık ortalamalardan çizilen küçük çizgi grafik. Tıklanınca o seçim açılır.
function Tile({ item, label, unit, selected, onSelect }: {
  item: OverviewItem
  label: string
  unit: string
  selected: boolean
  onSelect: () => void
}) {
  const rate = item.sen_slope_per_decade ?? item.slope_per_decade
  if (item.error || rate === undefined) {
    return (
      <div className="rounded-lg border border-dashed p-3 text-xs text-muted-foreground">
        {label}: {t("notEnoughData")}
      </div>
    )
  }
  const kind = trendKind({ significant: !!item.significant, direction: item.direction ?? "" })
  const Icon = TREND_ICON[kind]
  const color = TREND_COLOR[kind]
  const textColor = TREND_TEXT[kind]
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        "w-full rounded-lg border bg-card p-3 text-left transition-colors hover:bg-muted/60",
        selected && "border-brand ring-1 ring-brand",
      )}
    >
      <div className="flex items-center justify-between gap-2 text-sm font-medium">
        {label}
        {selected && <span className="text-xs font-normal text-muted-foreground">{t("selected")}</span>}
      </div>
      <div className="mt-1 flex items-center gap-1 text-sm font-semibold" style={{ color: textColor }}>
        <Icon className="size-4" />
        {trendText(kind)}
      </div>
      <div className="text-xs text-muted-foreground">
        {fmt(rate, 2, true)} {t("perDecadeUnit", { unit })}
      </div>
      <div className="mt-2 h-10">
        <ResponsiveContainer width="100%" height={40} initialDimension={{ width: 200, height: 40 }}>
          <LineChart data={item.yearly}>
            <YAxis hide domain={["dataMin", "dataMax"]} />
            <Line dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </button>
  )
}

// "Tüm bölgeler bir bakışta": her bölge için bir satır, her ölçüm için bir kutu.
// Hangi bölgede neyin arttığını/azaldığını tek ekranda gösterir.
export function OverviewGrid({ meta, items, regionId, variableId, onSelect }: {
  meta: Meta
  items: OverviewItem[]
  regionId: string
  variableId: string
  onSelect: (regionId: string, variableId: string) => void
}) {
  const find = (r: string, v: string) => items.find((i) => i.region_id === r && i.variable_id === v)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("overviewTitle")}</CardTitle>
        <CardDescription>{t("overviewHint")}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        {meta.regions.map((region) => (
          <div key={region.id} className="space-y-2">
            <h3 className="font-heading text-base font-semibold">{regionName(region)}</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              {meta.variables.map((variable) => {
                const item = find(region.id, variable.id)
                if (!item) return null
                return (
                  <Tile
                    key={variable.id}
                    item={item}
                    label={variableName(variable)}
                    unit={variableUnit(variable)}
                    selected={region.id === regionId && variable.id === variableId}
                    onSelect={() => onSelect(region.id, variable.id)}
                  />
                )
              })}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
