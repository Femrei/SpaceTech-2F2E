// Trend colours and icons shared by the KPI tiles, chart and overview grid.
import { ArrowDownRightIcon, ArrowUpRightIcon, MinusIcon } from "lucide-react"

import type { Trend } from "@/lib/content"
import { t } from "@/lib/i18n"

// Renk körlüğüne uygun turuncu/mavi çifti (değerleri index.css'te, tema başına).
// Anlam hiçbir zaman sadece renkle verilmez: her yerde ok simgesi ve yazı da kullanılır.
// TREND_COLOR grafik çizgileri ve işaretler içindir; yazıda TREND_TEXT kullanılır,
// çünkü onun tonları her iki temada da en az 4,5:1 kontrast verir.
export const TREND_COLOR: Record<Trend, string> = {
  up: "var(--trend-up)",
  down: "var(--trend-down)",
  flat: "var(--trend-flat)",
}

export const TREND_TEXT: Record<Trend, string> = {
  up: "var(--trend-up-text)",
  down: "var(--trend-down-text)",
  flat: "var(--trend-flat-text)",
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
