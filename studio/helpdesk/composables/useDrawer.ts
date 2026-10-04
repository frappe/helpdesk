import { reactive, ref, watch } from 'vue'
import { onKeyStroke, useScrollLock } from '@vueuse/core'

// Reactive, so blocks bind `drawer.open` without `.value`.
export function useDrawer(route) {
  const open = ref(false)
  const scrollLock = useScrollLock(document.body)

  watch(open, (value) => (scrollLock.value = value))
  watch(() => route.fullPath, close)
  onKeyStroke('Escape', () => open.value && close())

  function toggle() {
    open.value = !open.value
  }

  function close() {
    open.value = false
  }

  return reactive({ open, toggle, close })
}
