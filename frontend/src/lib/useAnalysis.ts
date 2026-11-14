import { useEffect, useState } from "react"

import {
  ApiError,
  fetchAnalysis,
  fetchBoxAnalysis,
  fetchCompare,
  fetchPointAnalysis,
  type PointAnalysis,
} from "@/lib/api"
import { t } from "@/lib/i18n"

type State<T> = { key: string; data?: T; error?: string } | null

// API hatasını kullanıcıya gösterilecek Türkçe/İngilizce mesaja çevirir.
function errorMessage(e: unknown): string {
  if (e instanceof ApiError && e.status === 422) return e.message.includes("only measured over land")
    ? t("placeNoLand")
    : `${t("notEnoughData")} ${e.message}`
  if (e instanceof ApiError && e.status === 502) return t("placeFetchError")
  return t("loadError")
}

// Üç hook'un ortak mantığı: "key" ile tanımlanan seçim için request() ile veriyi çeker.
// Dönen değer: { data } yüklendiyse, { error } hata varsa, null hâlâ yükleniyorsa.
// Seçim değişince önceki isteğin cevabı artık yok sayılır (stale = true): yavaş gelen
// eski bir cevap, yeni seçimin cevabının üzerine yazıp ekranı "yükleniyor"da
// bırakamaz. Ayrıca her cevap kendi anahtarıyla saklanır; seçim değiştiği anda eski
// sonuç gösterilmez.
function useKeyedFetch<T>(key: string | null, request: () => Promise<T>): State<T> {
  const [state, setState] = useState<State<T>>(null)

  useEffect(() => {
    if (key === null) return
    let stale = false
    request()
      .then((data) => { if (!stale) setState({ key, data }) })
      .catch((e: unknown) => { if (!stale) setState({ key, error: errorMessage(e) }) })
    return () => { stale = true }
    // request her çizimde yeni bir fonksiyon; isteği yalnızca seçim (key) değişince yenile.
  }, [key])

  return key !== null && state?.key === key ? state : null
}

// Bir bölge + değişken için analizi backend'den çeker (Pano, Dedektif Modu, Vaka Dosyaları).
export function useAnalysis(regionId: string, variableId: string, enabled = true) {
  return useKeyedFetch(enabled ? `${regionId}/${variableId}` : null, () => fetchAnalysis(regionId, variableId))
}

// Karşılaştır sekmesi için aynı mantık: iki bölgenin karşılaştırmasını çeker.
export function useComparison(variableId: string, regionA: string, regionB: string, enabled = true) {
  return useKeyedFetch(
    enabled ? `${variableId}/${regionA}/${regionB}` : null,
    () => fetchCompare(variableId, regionA, regionB),
  )
}

// "Konumunu seç" sekmesindeki seçim: tek bir nokta ya da çizilen bir kare.
export type PlaceSelection =
  | { kind: "point"; lat: number; lon: number }
  | { kind: "box"; south: number; west: number; north: number; east: number }

// DENEME – "Konumunu seç" sekmesi: seçilen nokta ya da kare için NASA POWER analizini
// çeker. Seçim yoksa (null; ör. henüz kare çizilmedi) hiçbir şey yapmaz ve null döner.
export function usePlaceAnalysis(selection: PlaceSelection | null, variableId: string) {
  return useKeyedFetch<PointAnalysis>(
    selection ? `${JSON.stringify(selection)}/${variableId}` : null,
    () => selection?.kind === "point"
      ? fetchPointAnalysis(selection.lat, selection.lon, variableId)
      : fetchBoxAnalysis(selection as Extract<PlaceSelection, { kind: "box" }>, variableId),
  )
}
