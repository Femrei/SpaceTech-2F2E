import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import App from "@/App"
import { TooltipProvider } from "@/components/ui/tooltip"
import "@/index.css"

// Sistemin açık/koyu tema ayarını takip eder: koyu temada <html>'e "dark"
// sınıfı eklenir, shadcn renkleri buna göre değişir.
function followSystemTheme() {
  const media = window.matchMedia("(prefers-color-scheme: dark)")
  const apply = () => document.documentElement.classList.toggle("dark", media.matches)
  apply()
  media.addEventListener("change", apply)
}

followSystemTheme()

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <TooltipProvider>
      <App />
    </TooltipProvider>
  </StrictMode>,
)
