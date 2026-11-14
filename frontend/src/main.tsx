import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import App from "@/App"
import { TooltipProvider } from "@/components/ui/tooltip"
import "@/index.css"
import { initTheme } from "@/lib/theme"

// Tema: varsayılan olarak sistem ayarı; üst çubuktaki düğmeyle değiştirilebilir.
initTheme()

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <TooltipProvider>
      <App />
    </TooltipProvider>
  </StrictMode>,
)
