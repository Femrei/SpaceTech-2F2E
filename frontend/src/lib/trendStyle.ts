// Trend colours and icons shared by the KPI tiles, chart and overview grid.
import { ArrowDownRightIcon, ArrowUpRightIcon, MinusIcon } from "lucide-react"

import type { Trend } from "@/lib/content"
import { t } from "@/lib/i18n"

// Renk körlüğüne uygun turuncu/mavi çifti. Anlam hiçbir zaman sadece renkle
// verilmez: her yerde ok simgesi ve yazı da kullanılır.
export const TREND_COLOR: Record<Trend, string> = {
  up: "#D55E00",
  down: "#0072B2",
  flat: "#8C8C8C",
}

// Her durum için ok simgesi: ↗ artıyor, ↘ azalıyor, — belirgin değişim yok.
export const TREND_ICON = {
  up: ArrowUpRightIcon,
  down: ArrowDownRightIcon,
  flat: MinusIcon,
} as const

// Duruma karşılık gelen kısa yazı ("Artıyor", "Azalıyor", "Belirgin değişim yok").
export function trendText(kind: Trend): string {
  return kind === "up" ? t("up") : kind === "down" ? t("down") : t("flat")
}
