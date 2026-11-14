import "leaflet/dist/leaflet.css"
import { MapContainer, Rectangle, TileLayer, Tooltip } from "react-leaflet"
import type { LatLngBoundsExpression } from "leaflet"

import type { Region } from "@/lib/api"
import { regionName } from "@/lib/content"
import { t } from "@/lib/i18n"
import { cn } from "@/lib/utils"

const SELECTED = "#2563eb"
const OTHER = "#64748b"

// Katalogdaki bbox'ı [Batı, Güney, Doğu, Kuzey] Leaflet'in beklediği
// [[Güney, Batı], [Kuzey, Doğu]] köşe biçimine çevirir.
function toBounds(bbox: Region["bbox"]): [[number, number], [number, number]] {
  const [w, s, e, n] = bbox
  return [[s, w], [n, e]]
}

// Bölgeleri OpenStreetMap üzerinde kutular olarak gösteren küçük harita
// (anahtar/token gerektirmez). Seçili bölge mavi ve dolu çizilir; diğerleri gri.
// onSelect verilirse kutuya tıklayınca o bölge seçilir.
export function RegionMap({ regions, selectedId, onSelect, className }: {
  regions: Region[]
  selectedId?: string
  onSelect?: (id: string) => void
  className?: string
}) {
  // Haritayı tüm bölgeleri kapsayacak şekilde açar (biraz kenar boşluğuyla).
  const all = regions.map((r) => toBounds(r.bbox))
  const bounds: LatLngBoundsExpression = [
    [Math.min(...all.map((b) => b[0][0])) - 1, Math.min(...all.map((b) => b[0][1])) - 1],
    [Math.max(...all.map((b) => b[1][0])) + 1, Math.max(...all.map((b) => b[1][1])) + 1],
  ]

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="region-map isolate h-48 overflow-hidden rounded-lg border sm:h-56">
        <MapContainer bounds={bounds} scrollWheelZoom={false} className="h-full w-full" attributionControl>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          {regions.map((r) => {
            const selected = r.id === selectedId
            return (
              <Rectangle
                key={`${r.id}-${selected}`}
                bounds={toBounds(r.bbox)}
                pathOptions={{
                  color: selected ? SELECTED : OTHER,
                  weight: selected ? 3 : 1.5,
                  fillOpacity: selected ? 0.3 : 0.1,
                  dashArray: selected ? undefined : "4 4",
                }}
                eventHandlers={onSelect ? { click: () => onSelect(r.id) } : undefined}
              >
                <Tooltip direction="top" permanent={selected}>
                  {regionName(r)}
                </Tooltip>
              </Rectangle>
            )
          })}
        </MapContainer>
      </div>
      {onSelect && <p className="text-xs text-muted-foreground">{t("mapHint")}</p>}
    </div>
  )
}
