// Light/dark theme: follows the operating system by default; the header toggle
// stores an explicit choice in localStorage so it survives reloads.
import { useSyncExternalStore } from "react"

type Theme = "light" | "dark"
const KEY = "etd-theme"
const media = window.matchMedia("(prefers-color-scheme: dark)")
const listeners = new Set<() => void>()

// Kullanıcının kaydettiği seçimi okur; yoksa (ya da tarayıcı depolamayı engelliyorsa) null.
function storedTheme(): Theme | null {
  try {
    const v = localStorage.getItem(KEY)
    return v === "light" || v === "dark" ? v : null
  } catch {
    return null
  }
}

// Geçerli tema: kayıtlı seçim varsa o, yoksa işletim sisteminin ayarı.
function currentTheme(): Theme {
  return storedTheme() ?? (media.matches ? "dark" : "light")
}

// Temayı sayfaya uygular (<html> üzerindeki "dark" sınıfı) ve dinleyenlere haber verir.
function apply() {
  document.documentElement.classList.toggle("dark", currentTheme() === "dark")
  listeners.forEach((fn) => fn())
}

// Uygulama açılırken bir kez çağrılır: temayı uygular ve sistem ayarı
// değişirse (kayıtlı seçim yoksa) otomatik takip eder.
export function initTheme() {
  apply()
  media.addEventListener("change", apply)
}

// Tema değişirken renk animasyonlarını bir kare için kapatır; yoksa her öğe
// kendi hızında renk değiştirir ve ekran bir an karışık görünür.
function withoutTransitions(change: () => void) {
  const root = document.documentElement
  root.classList.add("theme-switching")
  change()
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove("theme-switching")))
}

// Açık ↔ koyu arasında geçiş yapar ve seçimi kaydeder.
export function toggleTheme() {
  withoutTransitions(toggleNow)
}

function toggleNow() {
  const next: Theme = currentTheme() === "dark" ? "light" : "dark"
  try {
    localStorage.setItem(KEY, next)
  } catch {
    // Depolama kapalıysa seçim sadece bu oturumda geçerli olur.
    document.documentElement.classList.toggle("dark", next === "dark")
    listeners.forEach((fn) => fn())
    return
  }
  apply()
}

// Bileşenlerin geçerli temayı okuyup değişince yeniden çizilmesini sağlar.
export function useTheme(): Theme {
  return useSyncExternalStore(
    (fn) => {
      listeners.add(fn)
      return () => listeners.delete(fn)
    },
    () => (document.documentElement.classList.contains("dark") ? "dark" : "light"),
  )
}
