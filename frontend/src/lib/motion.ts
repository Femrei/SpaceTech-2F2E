// Kaydırma animasyonu: kullanıcı işletim sisteminde "hareketi azalt" seçtiyse
// yumuşak kaydırma yerine anında atlar (prefers-reduced-motion).
export function scrollBehavior(): ScrollBehavior {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth"
}
