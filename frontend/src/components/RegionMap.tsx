import "leaflet/dist/leaflet.css"
import { useEffect, useMemo } from "react"
import { MapContainer, Rectangle, TileLayer, Tooltip, useMap } from "react-leaflet"
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

// Harita kutusunun boyutu değişince (sekme açılınca, pencere/düzen değişince)
// Leaflet'e yeni boyutu bildirir ve bölgeleri yeniden çerçeveye sığdırır.
// Leaflet boyutu sadece açılışta ölçtüğü için bu olmadan karolar eski genişlikte
// kalır ve haritanın bir kısmı boş görünür. Karolar normal çözünürlükte yeniden
// yüklenir, yani görüntü kalitesi bozulmaz.
function FitToContainer({ bounds }: { bounds: LatLngBoundsExpression }) {
  const map = useMap()
  useEffect(() => {
    const el = map.getContainer()
    let last = ""
    const observer = new ResizeObserver(() => {
      const { width, height } = el.getBoundingClientRect()
      const size = `${Math.round(width)}x${Math.round(height)}`
      if (width === 0 || height === 0 || size === last) return // gizliyken ölçme
      last = size
      map.invalidateSize()
      map.fitBounds(bounds, { padding: [16, 16] })
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [map, bounds])
  return null
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
  // useMemo: aynı bölgeler için aynı nesne kalsın ki FitToContainer gereksiz yere yeniden kurulmasın.
  const bounds = useMemo<LatLngBoundsExpression>(() => {
    const all = regions.map((r) => toBounds(r.bbox))
    return [
      [Math.min(...all.map((b) => b[0][0])) - 0.5, Math.min(...all.map((b) => b[0][1])) - 0.5],
      [Math.max(...all.map((b) => b[1][0])) + 1, Math.max(...all.map((b) => b[1][1])) + 0.5],
    ]
  }, [regions])

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
          <FitToContainer bounds={bounds} />
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
