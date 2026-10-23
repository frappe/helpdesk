import { computed } from 'vue'
import { useStorage } from '@vueuse/core'

// Dismissal is remembered per ticket per day, so it returns tomorrow.
export function useOutsideHoursBanner(ticket) {
  const banner = computed(() => ticket.data?.outside_hours_banner)
  const isDismissed = useStorage(() => dismissKey(ticket.data?.name), false, localStorage, {
    writeDefaults: false,
  })

  function dismissKey(name: string) {
    return `kb:banner-dismissed:${name}:${new Date().toISOString().split('T')[0]}`
  }

  function dismissBanner() {
    isDismissed.value = true
  }

  return {
    showBanner: computed(() => Boolean(banner.value?.show) && !isDismissed.value),
    bannerMessage: computed(() => banner.value?.msg || ''),
    dismissBanner,
  }
}
