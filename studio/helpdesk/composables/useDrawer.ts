import { reactive, watch } from 'vue'
import { onKeyStroke, useScrollLock } from '@vueuse/core'

// Reactive, so blocks bind `drawer.open` without `.value`.
export function useDrawer(route) {
  const open = useScrollLock(document.body)
  // Close returns focus to the opener.
  let opener: HTMLElement | null = null
  watch(() => route.fullPath, close)
  onKeyStroke('Escape', () => open.value && close())

  function toggle() {
    if (open.value) return close()
    opener = document.activeElement as HTMLElement | null
    open.value = true
  }

  function close() {
    if (!open.value) return
    open.value = false
    opener?.focus()
    opener = null
  }

  return reactive({ open, toggle, close })
}

// State only, for a frappe-ui `BottomSheet`, which locks scroll, closes on
// Escape and returns focus itself. A second scroll lock would leave the page
// locked after the sheet closes.
export function useBottomSheet(route) {
  const sheet = reactive({
    open: false,
    toggle: () => (sheet.open = !sheet.open),
    close: () => (sheet.open = false),
  })
  watch(() => route.fullPath, sheet.close)
  return sheet
}
