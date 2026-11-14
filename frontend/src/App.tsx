import { useEffect, useState } from "react"
import {
  CompassIcon,
  ConstructionIcon,
  FolderOpenIcon,
  ScaleIcon,
  SearchIcon,
  SatelliteIcon,
  TriangleAlertIcon,
} from "lucide-react"

import { ExploreTab } from "@/components/ExploreTab"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { fetchMeta, type Meta } from "@/lib/api"
import { t } from "@/lib/i18n"

// Henüz yapılmamış sekmeler için "yakında" bilgi kutusu gösterir.
function ComingSoon({ what }: { what: string }) {
  return (
    <Alert>
      <ConstructionIcon />
      <AlertDescription>{t("comingSoon", { what, explore: t("tabExplore") })}</AlertDescription>
    </Alert>
  )
}

// Sayfanın tamamı: başlık -> (stub uyarısı) -> 4 sekme -> altbilgi (veri kaynağı).
// Açılışta backend'den katalog vb. bilgileri (meta) bir kez çeker.
export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    fetchMeta().then(setMeta).catch(() => setFailed(true))
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
      <header className="space-y-2">
        <h1 className="flex items-center gap-3 text-3xl font-bold tracking-tight sm:text-4xl">
          <SatelliteIcon className="size-8 shrink-0" />
          {t("appTitle")}
        </h1>
        <p className="text-muted-foreground">{t("tagline")}</p>
      </header>

      {meta && meta.stubs_in_use.length > 0 && (
        <Alert className="border-amber-500/50 text-amber-700 dark:text-amber-400">
          <TriangleAlertIcon />
          <AlertTitle>{t("stubWarningTitle")}</AlertTitle>
          <AlertDescription className="text-amber-700/90 dark:text-amber-400/90">
            {t("stubWarning", { modules: meta.stubs_in_use.join(", ") })}
          </AlertDescription>
        </Alert>
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
          <TabsList className="h-auto flex-wrap">
            <TabsTrigger value="detective"><SearchIcon />{t("tabDetective")}</TabsTrigger>
            <TabsTrigger value="explore"><CompassIcon />{t("tabExplore")}</TabsTrigger>
            <TabsTrigger value="cases"><FolderOpenIcon />{t("tabCases")}</TabsTrigger>
            <TabsTrigger value="compare"><ScaleIcon />{t("tabCompare")}</TabsTrigger>
          </TabsList>
          <TabsContent value="detective"><ComingSoon what={t("tabDetective")} /></TabsContent>
          <TabsContent value="explore"><ExploreTab meta={meta} /></TabsContent>
          <TabsContent value="cases"><ComingSoon what={t("tabCases")} /></TabsContent>
          <TabsContent value="compare"><ComingSoon what={t("tabCompare")} /></TabsContent>
        </Tabs>
      )}

      <footer className="space-y-4 pt-4">
        <Separator />
        {meta && (
          <p className="text-xs text-muted-foreground">
            {t("footer", {
              datasets: meta.variables.map((v) => v.dataset).join(" · "),
              date: meta.data_downloaded_on,
            })}
          </p>
        )}
      </footer>
    </div>
  )
}
