import { useEffect, useState } from "react"
import {
  FolderOpenIcon,
  LayoutDashboardIcon,
  SatelliteIcon,
  ScaleIcon,
  SearchIcon,
  TriangleAlertIcon,
} from "lucide-react"

import { AboutSheet } from "@/components/AboutSheet"
import { CasesTab } from "@/components/CasesTab"
import { CompareTab } from "@/components/CompareTab"
import { Dashboard } from "@/components/Dashboard"
import { DetectiveTab } from "@/components/DetectiveTab"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { fetchMeta, type Meta } from "@/lib/api"
import { t } from "@/lib/i18n"

// Sekme içerikleri gizlense de bellekte kalır (forceMount); böylece örneğin
// Dedektif Modu'ndaki ilerleme sekme değiştirince kaybolmaz.
const PANEL = "data-[state=inactive]:hidden"

// Sayfanın tamamı: üst bar (logo + başlık + Hakkında) -> (geliştirme uyarısı)
// -> 4 sekme -> altbilgi (veri kaynağı). Açılışta backend'den katalog vb.
// bilgileri (meta) bir kez çeker.
export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    fetchMeta().then(setMeta).catch(() => setFailed(true))
  }, [])

  return (
    <div className="min-h-svh bg-muted/40">
      <header className="sticky top-0 z-20 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 sm:px-6">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <SatelliteIcon className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-base font-semibold leading-tight sm:text-lg">{t("appTitle")}</h1>
            <p className="truncate text-xs text-muted-foreground sm:text-sm">{t("appSubtitle")}</p>
          </div>
          {meta && <AboutSheet downloadedOn={meta.data_downloaded_on} />}
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-5 px-4 py-6 sm:px-6">
        {meta && (meta.mock_data || meta.stubs_in_use.length > 0) && (
          <p className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-800 dark:text-amber-300">
            <TriangleAlertIcon className="mt-0.5 size-3.5 shrink-0" />
            <span>
              {meta.stubs_in_use.length > 0 && `${t("stubWarning", { modules: meta.stubs_in_use.join(", ") })} `}
              {meta.mock_data && t("mockDataWarning")}
            </span>
          </p>
        )}

        {failed ? (
          <Alert variant="destructive">
            <TriangleAlertIcon />
            <AlertDescription>{t("loadError")}</AlertDescription>
          </Alert>
        ) : !meta ? (
          <Skeleton className="h-96 w-full" />
        ) : (
          <Tabs defaultValue="explore" className="gap-5">
            <TabsList variant="line" className="h-auto w-full flex-wrap justify-start gap-1 border-b px-0 pb-1">
              <TabsTrigger className="h-10 flex-none px-3" value="explore"><LayoutDashboardIcon />{t("tabExplore")}</TabsTrigger>
              <TabsTrigger className="h-10 flex-none px-3" value="detective"><SearchIcon />{t("tabDetective")}</TabsTrigger>
              <TabsTrigger className="h-10 flex-none px-3" value="cases"><FolderOpenIcon />{t("tabCases")}</TabsTrigger>
              <TabsTrigger className="h-10 flex-none px-3" value="compare"><ScaleIcon />{t("tabCompare")}</TabsTrigger>
            </TabsList>
            <TabsContent value="explore" forceMount className={PANEL}><Dashboard meta={meta} /></TabsContent>
            <TabsContent value="detective" forceMount className={PANEL}><DetectiveTab meta={meta} /></TabsContent>
            <TabsContent value="cases" forceMount className={PANEL}>
              <CasesTab meta={meta} mock={meta.stubs_in_use.some((s) => s.startsWith("detective"))} />
            </TabsContent>
            <TabsContent value="compare" forceMount className={PANEL}><CompareTab meta={meta} /></TabsContent>
          </Tabs>
        )}
      </main>

      <footer className="mx-auto max-w-7xl px-4 pb-8 sm:px-6">
        {meta && (
          <p className="border-t pt-4 text-xs text-muted-foreground">
            {t("footer", {
              datasets: meta.variables.map((v) => v.dataset).join(", "),
              date: meta.data_downloaded_on,
            })}
          </p>
        )}
      </footer>
    </div>
  )
}
