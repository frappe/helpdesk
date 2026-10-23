import { computed, ref } from 'vue'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)

  // Sent even when empty: an origin marks a portal ticket. Not `origin`: that is
  // window.origin (the site URL) whenever this script fails to load.
  const { from, article, q, utm_source } = route?.query || {}
  const ticketOrigin = { from, article, q, utm_source }
  // Subject holds 140 chars; longer would block submit.
  const initialSubject = String(q || '').trim().slice(0, 140)

  const customActions = ref([])
  const timeFormat = computed(() => settings.config.value?.time_format)

  return {
    ...settings,
    initialSubject,
    ticketOrigin,
    timeFormat,
    customActions,
    setActions: (actions) => (customActions.value = actions),
    // Replace: Back from the new ticket goes where the form was opened from.
    openTicket: (ticket) => navigateTo(ROUTES.ticket(ticket.name), { replace: true }),
  }
}
