import { computed, watch } from 'vue'
import { useStorage } from '@vueuse/core'
import { createResource } from 'frappe-ui'

// Dismissal is remembered per ticket per day, so it returns tomorrow.
export function useOutsideHoursBanner(ticket) {
  const banner = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.show_outside_hours_banner',
    makeParams: () => ({ ticket_name: ticket.data?.name }),
  })
  const isDismissed = useStorage(() => dismissKey(ticket.data?.name), false, localStorage, {
    writeDefaults: false,
  })

  watch(
    () => ticket.data?.name,
    (name) => name && banner.fetch(),
    { immediate: true },
  )

  function dismissKey(name: string) {
    return `kb:banner-dismissed:${name}:${new Date().toISOString().split('T')[0]}`
  }

  function dismissBanner() {
    isDismissed.value = true
  }

  return {
    showBanner: computed(() => Boolean(banner.data?.show) && !isDismissed.value),
    bannerMessage: computed(() => banner.data?.msg || ''),
    dismissBanner,
  }
}
