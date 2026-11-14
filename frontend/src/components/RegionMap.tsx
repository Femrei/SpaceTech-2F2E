import "leaflet/dist/leaflet.css"
import { MapContainer, Rectangle, TileLayer, Tooltip } from "react-leaflet"
import type { LatLngBoundsExpression } from "leaflet"

import type { Region } from "@/lib/api"
import { regionName } from "@/lib/content"
import { t } from "@/lib/i18n"
import { cn } from "@/lib/utils"

const SELECTED = "#2563eb"
const OTHER = "#94a3b8"

// Katalogdaki bbox'ı [Batı, Güney, Doğu, Kuzey] Leaflet'in beklediği
// [[Güney, Batı], [Kuzey, Doğu]] köşe biçimine çevirir.
function toBounds(bbox: Region["bbox"]): [[number, number], [number, number]] {
  const [w, s, e, n] = bbox
  return [[s, w], [n, e]]
}

// Bölgeleri OpenStreetMap üzerinde kutular olarak gösteren küçük harita
// (anahtar/token gerektirmez). Seçili bölge mavi ve dolu çizilir; diğerleri gri.
// onSelect verilirse kutuya tıklayınca o bölge seçilir.
// mapClassName ile haritanın yüksekliği değiştirilebilir (Pano'da büyük gösterilir).
export function RegionMap({ regions, selectedId, onSelect, className, mapClassName = "h-48 sm:h-56" }: {
  regions: Region[]
  selectedId?: string
  onSelect?: (id: string) => void
  className?: string
  mapClassName?: string
}) {
  // Haritayı tüm bölgeleri kapsayacak şekilde açar (etiketlere yer kalsın diye
  // üstte biraz daha fazla boşlukla).
  const all = regions.map((r) => toBounds(r.bbox))
  const bounds: LatLngBoundsExpression = [
    [Math.min(...all.map((b) => b[0][0])) - 0.5, Math.min(...all.map((b) => b[0][1])) - 0.5],
    [Math.max(...all.map((b) => b[1][0])) + 1, Math.max(...all.map((b) => b[1][1])) + 0.5],
  ]

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className={cn("region-map isolate overflow-hidden rounded-lg border", mapClassName)}>
        <MapContainer
          bounds={bounds}
          boundsOptions={{ padding: [16, 16] }}
          zoomSnap={0.25}
          scrollWheelZoom={false}
          className="h-full w-full"
          attributionControl
        >
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
                  weight: selected ? 3 : 2,
                  fillOpacity: selected ? 0.3 : 0.15,
                  dashArray: selected ? undefined : "6 4",
                }}
                eventHandlers={onSelect ? { click: () => onSelect(r.id) } : undefined}
              >
                {/* Her bölgenin adı haritada sürekli görünür; seçili olan kalın yazılır. */}
                <Tooltip direction="top" permanent className={selected ? "font-semibold" : "opacity-80"}>
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
