import { shallowRef } from 'vue'

// Pages pass their router; the editor passes a readonly proxy.
const router = shallowRef<any>(null)

export function bindRouter(value: unknown) {
  if (value) router.value = value
}

// A page script's router proxy unwraps refs.
export function currentRoute() {
  return router.value?.currentRoute?.value || router.value?.currentRoute || {}
}

export function navigateTo(location: unknown, { replace = false } = {}) {
  return replace ? router.value?.replace(location) : router.value?.push(location)
}

export function afterEachRoute(handler: (to: any) => void) {
  router.value?.afterEach(handler)
}

export function navigateBack() {
  return router.value?.back()
}

export function previousLocation(): string | null {
  const previous = router.value?.options?.history?.state?.back
  return typeof previous === 'string' ? previous : null
}
