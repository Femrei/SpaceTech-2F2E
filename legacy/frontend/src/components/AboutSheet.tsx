import { InfoIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { t } from "@/lib/i18n"

// Üst bardaki "Hakkında" butonu ve açılan yan panel. Üç bölüm:
// Hakkında (uygulama ne yapar), Nasıl çalışır? (4 adım), Veri kaynakları
// (3 veri seti + indirme tarihi) ve "Akılda tut" (sınırlılıklar).
export function AboutSheet({ downloadedOn }: { downloadedOn: string }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          <InfoIcon />
          <span className="hidden sm:inline">{t("about")}</span>
        </Button>
      </SheetTrigger>
      <SheetContent className="w-full overflow-y-auto sm:max-w-md">
        <SheetHeader>
          <SheetTitle>{t("aboutTitle")}</SheetTitle>
          <SheetDescription className="leading-relaxed">{t("aboutText")}</SheetDescription>
        </SheetHeader>
        <div className="space-y-6 px-4 pb-6 text-sm">
          <section className="space-y-2">
            <h3 className="font-semibold">{t("howItWorks")}</h3>
            <ol className="list-decimal space-y-1.5 pl-5 text-muted-foreground">
              <li>{t("how1")}</li>
              <li>{t("how2")}</li>
              <li>{t("how3")}</li>
              <li>{t("how4")}</li>
            </ol>
          </section>
          <section className="space-y-2">
            <h3 className="font-semibold">{t("dataSources")}</h3>
            <ul className="list-disc space-y-1.5 pl-5 text-muted-foreground">
              <li>{t("sourcePrecip")}</li>
              <li>{t("sourceSoil")}</li>
              <li>{t("sourceTemp")}</li>
            </ul>
            <p className="text-muted-foreground">{t("sourceAccess", { date: downloadedOn })}</p>
          </section>
          <section className="space-y-2">
            <h3 className="font-semibold">{t("limitsTitle")}</h3>
            <p className="text-muted-foreground">{t("limitsText")}</p>
          </section>
        </div>
      </SheetContent>
    </Sheet>
  )
}
