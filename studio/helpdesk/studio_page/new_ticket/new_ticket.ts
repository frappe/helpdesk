import { computed, ref } from 'vue'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)

  // Sent even when empty: an origin marks a portal ticket.
  const { from, article, q } = route?.query || {}
  const origin = { from, article, q }
  // Subject holds 140 chars; longer would block submit.
  const initialSubject = String(q || '').trim().slice(0, 140)

  const customActions = ref([])
  const timeFormat = computed(() => settings.config.value?.time_format)

  return {
    ...settings,
    initialSubject,
    origin,
    timeFormat,
    customActions,
    setActions: (actions) => (customActions.value = actions),
    openTicket: (ticket) => navigateTo(ROUTES.ticket(ticket.name)),
  }
}
