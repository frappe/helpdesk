import { computed, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
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
  const draft = String(route?.query?.draft || '')

  watch(
    settings.config,
    (config) => {
      if (config && settings.isGuest.value && !settings.canCreateTicket.value) settings.signIn()
    },
    { immediate: true },
  )

  const customActions = ref([])
  const timeFormat = computed(() => settings.config.value?.time_format)
  const submittedEmail = ref('')

  return {
    ...settings,
    initialSubject,
    origin,
    draft,
    timeFormat,
    customActions,
    submittedEmail,
    receipt: computed(() => __("Thanks, we'll be in touch at {0}.", [submittedEmail.value])),
    setActions: (actions) => (customActions.value = actions),
    openTicket: (ticket) => navigateTo(ROUTES.ticket(ticket.name)),
    showReceipt: (email) => (submittedEmail.value = email),
  }
}
