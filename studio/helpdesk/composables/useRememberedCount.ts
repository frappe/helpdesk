import { watch } from 'vue'

// How many items a list showed last time, so its skeleton takes the same space.
export function useRememberedCount(key: string, count: () => number | undefined, fallback: number) {
  let remembered = fallback
  try {
    const stored = localStorage.getItem(key)
    if (stored !== null) remembered = Number(stored) || 0
  } catch {}
  watch(count, (value) => {
    if (value == null) return
    try {
      localStorage.setItem(key, String(value))
    } catch {}
  }, { immediate: true })
  return remembered
}
