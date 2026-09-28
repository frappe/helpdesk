import { computed, ref, watch } from 'vue'
import { createResource } from 'frappe-ui'

// Dismissal is remembered per ticket per day, so it returns tomorrow.
export function useOutsideHoursBanner(ticket) {
  const banner = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.show_outside_hours_banner',
    makeParams: () => ({ ticket_name: ticket.data?.name }),
  })
  const dismissed = ref(false)

  watch(
    () => ticket.data?.name,
    (name) => {
      if (!name) return
      dismissed.value = localStorage.getItem(dismissKey(name)) === 'true'
      banner.fetch()
    },
    { immediate: true },
  )

  function dismissKey(name: string) {
    return `kb:banner-dismissed:${name}:${new Date().toISOString().split('T')[0]}`
  }

  function dismissBanner() {
    localStorage.setItem(dismissKey(ticket.data.name), 'true')
    dismissed.value = true
  }

  return {
    showBanner: computed(() => Boolean(banner.data?.show) && !dismissed.value),
    bannerMessage: computed(() => banner.data?.msg || ''),
    dismissBanner,
  }
}
