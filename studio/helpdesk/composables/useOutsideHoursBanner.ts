import { computed } from 'vue'
import { useStorage } from '@vueuse/core'
import { dayjsLocal } from 'frappe-ui'

// Dismissed per ticket per day.
export function useOutsideHoursBanner(ticket) {
  const banner = computed(() => ticket.data?.outside_hours_banner)
  const isDismissed = useStorage(() => dismissKey(ticket.data?.name), false, localStorage, {
    writeDefaults: false,
  })

  function dismissKey(name: string) {
    // Local day: an ISO date rolls over at UTC midnight.
    return `kb:banner-dismissed:${name}:${dayjsLocal().format('YYYY-MM-DD')}`
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
