// Small building blocks shared by several tabs.
import type { ReactNode } from "react"
import { TriangleAlertIcon } from "lucide-react"

import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"

// Kullanıcıya sarı uyarı kutusu gösterir (veri yok, yetersiz veri vb.).
export function Warning({ children }: { children: ReactNode }) {
  return (
    <Alert>
      <TriangleAlertIcon />
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  )
}

// Etiketli açılır seçim kutusu (+ isteğe bağlı altında kısa açıklama).
// Listede isim görünür, arka planda id kullanılır.
export function Picker({ label, value, onChange, options, hint }: {
  label: string
  value: string
  onChange: (id: string) => void
  options: { id: string; name: string; disabled?: boolean }[]
  hint?: string
}) {
  return (
    <div className="grid content-start gap-1.5">
      <label className="text-sm font-medium">{label}</label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full" aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((o) => (
            <SelectItem key={o.id} value={o.id} disabled={o.disabled}>
              {o.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {hint && <p className="text-xs leading-relaxed text-muted-foreground">{hint}</p>}
    </div>
  )
}

// Veri yüklenirken gösterilen yer tutucu: 4 özet kutusu + büyük grafik alanı.
export function LoadingPanels() {
  return (
    <div className="space-y-4" aria-busy="true">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}
      </div>
      <Skeleton className="h-[420px] w-full" />
    </div>
  )
}
