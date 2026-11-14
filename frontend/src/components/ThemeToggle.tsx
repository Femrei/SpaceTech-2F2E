import { MoonIcon, SunIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { t } from "@/lib/i18n"
import { toggleTheme, useTheme } from "@/lib/theme"

// Üst çubuktaki açık/koyu tema düğmesi. Simge geçilecek temayı gösterir;
// ekran okuyucu için ne yapacağını söyleyen bir etiketi vardır.
export function ThemeToggle() {
  const theme = useTheme()
  const label = theme === "dark" ? t("toLight") : t("toDark")
  return (
    <Button variant="outline" size="icon-sm" onClick={toggleTheme} aria-label={label} title={label}>
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </Button>
  )
}
