// EXPERIMENT (owner: C): "Pick a place" tab – any point or hand-drawn box on Earth,
// NASA POWER data. To remove it: delete this file, its tab in App.tsx, power_loader.py
// and /api/point + /api/box in api.py.
import "leaflet/dist/leaflet.css"
import { useEffect, useMemo, useState } from "react"
import { CircleMarker, MapContainer, Rectangle, TileLayer, useMap, useMapEvents } from "react-leaflet"
import { LocateFixedIcon, MapPinIcon, SquareDashedIcon } from "lucide-react"

import { AnalysisPanels, SEGMENT } from "@/components/AnalysisBlock"
import { LoadingPanels, Picker, Warning } from "@/components/Common"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { Meta, Region } from "@/lib/api"
import { variableName, variableShort } from "@/lib/content"
import { LANG, t } from "@/lib/i18n"
import { usePlaceAnalysis, type PlaceSelection } from "@/lib/useAnalysis"

type LatLon = { lat: number; lon: number }
type Mode = "point" | "box"

// POWER'ın bölge servisi kutunun her kenarı için en fazla 10 derece kabul eder.
const MAX_BOX_DEG = 10

// Hazır örnek noktalar: farklı iklimlerden, ilginç sonuç veren yerler.
const EXAMPLES: { id: string; name: { en: string; tr: string }; lat: number; lon: number }[] = [
  { id: "konya", name: { en: "Konya", tr: "Konya" }, lat: 37.87, lon: 32.49 },
  { id: "istanbul", name: { en: "Istanbul", tr: "İstanbul" }, lat: 41.01, lon: 28.98 },
  { id: "svalbard", name: { en: "Svalbard", tr: "Svalbard" }, lat: 78.22, lon: 15.65 },
  { id: "amazon", name: { en: "Amazon", tr: "Amazon" }, lat: -3.12, lon: -60.02 },
  { id: "sahel", name: { en: "Sahel (Niamey)", tr: "Sahel (Niamey)" }, lat: 13.51, lon: 2.11 },
]

// Bir sayıyı 2 ondalıklı, dile uygun yazar (TR: 37,87 / EN: 37.87); işaret atılır.
function num(x: number): string {
  return Math.abs(x).toLocaleString(LANG === "tr" ? "tr-TR" : "en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// Enlem için yön harfi: kuzey (K/N) ya da güney (G/S).
function ns(lat: number): string {
  return lat >= 0 ? (LANG === "tr" ? "K" : "N") : (LANG === "tr" ? "G" : "S")
}

// Boylam için yön harfi: doğu (D/E) ya da batı (B/W).
function ew(lon: number): string {
  return lon >= 0 ? (LANG === "tr" ? "D" : "E") : (LANG === "tr" ? "B" : "W")
}

// Koordinatı okunur yazıya çevirir: 37.87, 32.49 -> "37,87° K, 32,49° D" (TR) / "37.87° N, 32.49° E".
function formatCoords({ lat, lon }: LatLon): string {
  return `${num(lat)}° ${ns(lat)}, ${num(lon)}° ${ew(lon)}`
}

// Kutuyu okunur yazıya çevirir: "37,00° K–39,00° K, 32,00° D–34,00° D".
function formatBox(b: Region["bbox"]): string {
  return `${num(b.south)}° ${ns(b.south)}–${num(b.north)}° ${ns(b.north)}, ` +
    `${num(b.west)}° ${ew(b.west)}–${num(b.east)}° ${ew(b.east)}`
}

// Bir sayıyı 2 ondalığa yuvarlar (koordinatlar; ~1 km hassasiyet yeterli, önbellek de bu anahtarla çalışır).
function round2(x: number): number {
  return Math.round(x * 100) / 100
}

// Nokta modunda haritaya tıklanınca tıklanan noktayı (2 ondalığa yuvarlanmış, boylam
// -180..180 aralığına sarılmış) üst bileşene bildirir.
function ClickToPick({ onPick }: { onPick: (p: LatLon) => void }) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng.wrap()
      onPick({ lat: round2(lat), lon: round2(lng) })
    },
  })
  return null
}

// Kare çizme modu: ilk tıklama bir köşeyi, ikinci tıklama karşı köşeyi belirler.
// Arada fare hareket ettikçe kesikli bir önizleme karesi çizilir (dokunmatik ekranda
// iki dokunuş yeterli). Haritayı sürüklemek tıklama sayılmaz, yani çizerken harita
// hâlâ kaydırılabilir. Kare 10 dereceden büyükse kabul edilmez, uyarı gösterilir.
function DrawBox({ corner, setCorner, onDone, onTooBig }: {
  corner: LatLon | null
  setCorner: (c: LatLon | null) => void
  onDone: (b: Region["bbox"]) => void
  onTooBig: (tooBig: boolean) => void
}) {
  const [hover, setHover] = useState<LatLon | null>(null)
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng.wrap()
      const p = { lat: round2(lat), lon: round2(lng) }
      if (!corner) {
        setCorner(p)
        return
      }
      const box = {
        south: Math.min(corner.lat, p.lat),
        north: Math.max(corner.lat, p.lat),
        west: Math.min(corner.lon, p.lon),
        east: Math.max(corner.lon, p.lon),
      }
      if (box.north - box.south > MAX_BOX_DEG || box.east - box.west > MAX_BOX_DEG) {
        onTooBig(true)
        return
      }
      if (box.north === box.south || box.east === box.west) return // aynı noktaya iki tık
      onTooBig(false)
      setCorner(null)
      setHover(null)
      onDone(box)
    },
    mousemove(e) {
      if (corner) setHover({ lat: e.latlng.lat, lon: e.latlng.lng })
    },
  })
  if (!corner) return null
  const end = hover ?? corner
  const tooBig = Math.abs(end.lat - corner.lat) > MAX_BOX_DEG || Math.abs(end.lon - corner.lon) > MAX_BOX_DEG
  return (
    <>
      <CircleMarker
        center={[corner.lat, corner.lon]}
        radius={5}
        pathOptions={{ color: "var(--brand)", fillColor: "var(--brand)", fillOpacity: 1 }}
        interactive={false}
      />
      {hover && (
        <Rectangle
          bounds={[[corner.lat, corner.lon], [end.lat, end.lon]]}
          pathOptions={{
            color: tooBig ? "var(--destructive)" : "var(--brand)",
            weight: 2,
            dashArray: "6 4",
            fillOpacity: 0.1,
          }}
          interactive={false}
        />
      )}
    </>
  )
}

// Seçilen nokta haritanın görünen alanı dışındaysa (örnek düğmesi, "Konumum")
// haritayı o noktaya götürür; haritanın kutusu boyut değiştirince (sekme ilk
// açıldığında, pencere daralınca) Leaflet'e yeni boyutu bildirir.
function FollowPoint({ point }: { point: LatLon | null }) {
  const map = useMap()
  useEffect(() => {
    if (point && !map.getBounds().pad(-0.1).contains([point.lat, point.lon])) {
      map.setView([point.lat, point.lon], Math.max(map.getZoom(), 5))
    }
  }, [map, point])
  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize())
    observer.observe(map.getContainer())
    return () => observer.disconnect()
  }, [map])
  return null
}

// "Konumunu seç" sekmesi, yukarıdan aşağıya:
//   1) Ölçüm seçimi + seçim şekli (Nokta / Kare çiz) + örnek noktalar + "Konumum"
//   2) Dünya haritası: nokta modunda tıklanan nokta ve verinin geldiği ızgara hücresi,
//      kare modunda kullanıcının iki tıklamayla çizdiği kare
//   3) Pano ile aynı analiz görünümü (özet kutuları, grafik, "Bu ne demek?")
// Veri NASA POWER'dan backend üzerinden gelir (/api/point, /api/box); analiz B'nin aynı kodudur.
export function PlaceTab({ meta }: { meta: Meta }) {
  const variables = meta.point_variables ?? []
  const [variableId, setVariableId] = useState(variables[0]?.id ?? "")
  const [mode, setMode] = useState<Mode>("point")
  const [point, setPoint] = useState<LatLon>({ lat: EXAMPLES[0].lat, lon: EXAMPLES[0].lon })
  const [box, setBox] = useState<Region["bbox"] | null>(null)
  const [corner, setCorner] = useState<LatLon | null>(null)
  const [tooBig, setTooBig] = useState(false)
  const [locating, setLocating] = useState<"idle" | "busy" | "error">("idle")

  // Analizi istenen seçim: nokta modunda nokta, kare modunda (çizildiyse) kare.
  const selection = useMemo<PlaceSelection | null>(() => {
    if (mode === "point") return { kind: "point", ...point }
    return box ? { kind: "box", ...box } : null
  }, [mode, point, box])
  const state = usePlaceAnalysis(selection, variableId)
  const variable = variables.find((v) => v.id === variableId)
  const area = state?.data?.point.cell
  const nCells = state?.data?.point.n_cells ?? 1

  // AnalysisPanels bir "bölge" bekler: seçilen nokta ya da kare için ad ve kutu içeren
  // bir yer tanımı kurar.
  const place = useMemo<Region | null>(() => {
    if (!area || !selection) return null
    const name = selection.kind === "box"
      ? t("placeBoxName", { box: formatBox(selection) })
      : t("placeHere", { coords: formatCoords(selection) })
    const center = selection.kind === "box"
      ? { lat: (selection.south + selection.north) / 2, lon: (selection.west + selection.east) / 2 }
      : selection
    return { id: "point", name, bbox: area, lat: center.lat, lon: center.lon, description: "" }
  }, [area, selection])

  // Seçim şeklini değiştirir; yarım kalmış bir kare çizimini iptal eder.
  const changeMode = (m: Mode) => {
    setMode(m)
    setCorner(null)
    setTooBig(false)
  }

  // Örnek düğmesi ya da "Konumum": nokta moduna geçip o noktayı seçer.
  const pickPoint = (p: LatLon) => {
    changeMode("point")
    setPoint(p)
  }

  // Tarayıcıdan kullanıcının konumunu ister (izin verirse) ve o noktayı seçer.
  const pickMyLocation = () => {
    if (!navigator.geolocation) return setLocating("error")
    setLocating("busy")
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        pickPoint({ lat: round2(pos.coords.latitude), lon: round2(pos.coords.longitude) })
        setLocating("idle")
      },
      () => setLocating("error"),
      { timeout: 10000 },
    )
  }

  if (!variable) return <Warning>{t("loadError")}</Warning>

  const mapHint = mode === "point"
    ? t("placeMapHint")
    : tooBig ? t("placeBoxTooBig") : corner ? t("placeBoxHintSecond") : t("placeBoxHint")

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">{t("placeIntro")}</p>

      <Card size="sm">
        <CardContent className="space-y-4">
          <div className="grid content-start gap-4 sm:grid-cols-2">
            <Picker
              label={t("variable")}
              value={variableId}
              onChange={setVariableId}
              options={variables.map((v) => ({ id: v.id, name: variableName(v) }))}
              hint={variableShort(variable)}
            />
            <div className="grid content-start gap-3">
              <div className="grid content-start gap-1.5">
                <span className="text-sm font-medium">{t("placeMode")}</span>
                <Tabs value={mode} onValueChange={(v) => changeMode(v as Mode)}>
                  <TabsList>
                    <TabsTrigger value="point" className={SEGMENT}><MapPinIcon />{t("placeModePoint")}</TabsTrigger>
                    <TabsTrigger value="box" className={SEGMENT}><SquareDashedIcon />{t("placeModeBox")}</TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
              <div className="grid content-start gap-1.5">
                <span className="text-sm font-medium">{t("placeExamples")}</span>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLES.map((ex) => {
                    const active = mode === "point" && ex.lat === point.lat && ex.lon === point.lon
                    return (
                      <Button
                        key={ex.id}
                        size="sm"
                        variant={active ? "default" : "outline"}
                        aria-pressed={active}
                        onClick={() => pickPoint({ lat: ex.lat, lon: ex.lon })}
                      >
                        {ex.name[LANG]}
                      </Button>
                    )
                  })}
                  <Button size="sm" variant="ghost" onClick={pickMyLocation} disabled={locating === "busy"}>
                    <LocateFixedIcon />
                    {locating === "busy" ? t("placeLocating") : t("placeMyLocation")}
                  </Button>
                </div>
                {locating === "error" && <p className="text-xs text-muted-foreground">{t("placeLocateError")}</p>}
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="region-map isolate h-72 overflow-hidden rounded-lg border sm:h-96">
              <MapContainer
                center={[point.lat, point.lon]}
                zoom={5}
                minZoom={2}
                zoomSnap={0.25}
                scrollWheelZoom={false}
                worldCopyJump
                doubleClickZoom={mode === "point"}
                className="h-full w-full cursor-crosshair"
                attributionControl
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                <FollowPoint point={mode === "point" ? point : null} />
                {mode === "point" ? (
                  <>
                    <ClickToPick onPick={setPoint} />
                    {area && (
                      <Rectangle
                        bounds={[[area.south, area.west], [area.north, area.east]]}
                        pathOptions={{ color: "var(--brand)", weight: 2, fillOpacity: 0.2 }}
                        interactive={false}
                      />
                    )}
                    <CircleMarker
                      center={[point.lat, point.lon]}
                      radius={6}
                      pathOptions={{ color: "var(--brand)", fillColor: "var(--brand)", fillOpacity: 1, weight: 2 }}
                      interactive={false}
                    />
                  </>
                ) : (
                  <>
                    <DrawBox corner={corner} setCorner={setCorner} onDone={setBox} onTooBig={setTooBig} />
                    {box && !corner && (
                      <Rectangle
                        bounds={[[box.south, box.west], [box.north, box.east]]}
                        pathOptions={{ color: "var(--brand)", weight: 2, fillOpacity: 0.2 }}
                        interactive={false}
                      />
                    )}
                  </>
                )}
              </MapContainer>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-xs text-muted-foreground">
              <span role="status" className={tooBig && mode === "box" ? "font-medium text-destructive" : undefined}>
                {mapHint}
                {mode === "box" && corner && (
                  <button type="button" className="ml-2 underline underline-offset-2 hover:text-foreground" onClick={() => { setCorner(null); setTooBig(false) }}>
                    {t("placeBoxCancel")}
                  </button>
                )}
              </span>
              <span className="inline-flex items-center gap-1 font-mono">
                <MapPinIcon className="size-3.5" aria-hidden="true" />
                {mode === "point" ? formatCoords(point) : box ? formatBox(box) : "—"}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {!selection ? (
        <Warning>{t("placeBoxEmpty")}</Warning>
      ) : !state ? (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground" role="status">{t("placeLoading")}</p>
          <LoadingPanels />
        </div>
      ) : state.error || !state.data || !place ? (
        <Warning>{state.error ?? t("loadError")}</Warning>
      ) : (
        <AnalysisPanels
          meta={meta}
          region={place}
          variable={variable}
          data={state.data}
          caption={selection.kind === "box" ? t("placeBoxCaption", { n: String(nCells) }) : t("placeCaption")}
          note={t("placeNote")}
        />
      )}
    </div>
  )
}
