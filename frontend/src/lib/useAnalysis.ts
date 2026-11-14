import { useEffect, useState } from "react"

import { ApiError, fetchAnalysis, fetchCompare, type Analysis, type Comparison } from "@/lib/api"
import { t } from "@/lib/i18n"

type State<T> = { key: string; data?: T; error?: string } | null

// API hatasını kullanıcıya gösterilecek Türkçe/İngilizce mesaja çevirir.
function errorMessage(e: unknown): string {
  return e instanceof ApiError && e.status === 422 ? `${t("notEnoughData")} ${e.message}` : t("loadError")
}

// Bir bölge + değişken için analizi backend'den çeker.
// Dönen değer: { data } yüklendiyse, { error } hata varsa, null hâlâ yükleniyorsa.
// Cevap hangi seçime aitse o anahtarla saklanır; geç gelen eski bir cevap
// yeni seçimin yerine gösterilmez.
export function useAnalysis(regionId: string, variableId: string, enabled = true) {
  const key = `${regionId}/${variableId}`
  const [state, setState] = useState<State<Analysis>>(null)

  useEffect(() => {
    if (!enabled) return
    const k = `${regionId}/${variableId}`
    fetchAnalysis(regionId, variableId)
      .then((data) => setState({ key: k, data }))
      .catch((e: unknown) => setState({ key: k, error: errorMessage(e) }))
  }, [regionId, variableId, enabled])

  return state?.key === key ? state : null
}

// Karşılaştır sekmesi için aynı mantık: iki bölgenin karşılaştırmasını çeker.
export function useComparison(variableId: string, regionA: string, regionB: string, enabled = true) {
  const key = `${variableId}/${regionA}/${regionB}`
  const [state, setState] = useState<State<Comparison>>(null)

  useEffect(() => {
    if (!enabled) return
    const k = `${variableId}/${regionA}/${regionB}`
    fetchCompare(variableId, regionA, regionB)
      .then((data) => setState({ key: k, data }))
      .catch((e: unknown) => setState({ key: k, error: errorMessage(e) }))
  }, [variableId, regionA, regionB, enabled])

  return state?.key === key ? state : null
}
