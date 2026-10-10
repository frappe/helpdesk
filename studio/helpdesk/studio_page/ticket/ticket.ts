import { computed, ref, watch } from 'vue'
import { createResource, toast } from 'frappe-ui'
import { createToast, setupCustomizations } from '@helpdesk/shared/formScripts'
import { __ } from '@helpdesk/shared/translation'
import { useOutsideHoursBanner } from '@app/composables/useOutsideHoursBanner'
import { useReplyComposer } from '@app/composables/useReplyComposer'
import { useTicketDetails } from '@app/composables/useTicketDetails'
import { useTicketFeedback } from '@app/composables/useTicketFeedback'
import { useTicketThread } from '@app/composables/useTicketThread'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import {
  CLOSED_STATUS,
  isClosedStatus,
  loadTicketMeta,
} from '@app/stores/ticketMeta'
import { askConfirm, runAction, scriptDialog, updateTicket } from '@app/utils'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer shows the reader's own avatar, which rides on the settings payload.
  settings.loadSettings()
  loadTicketMeta()

  const ticketId = computed(() => String(route?.params?.name || ''))

  const customActions = ref([])

  const ticket = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_one',
    makeParams: () => ({ name: ticketId.value }),
    onSuccess: runFormScripts,
  })

  // HD Form Scripts get the desk portal's context, so scripts written for it keep working.
  async function runFormScripts(data) {
    await setupCustomizations(data, {
      doc: data,
      call: context.call,
      router: context.router,
      toast,
      createToast,
      $dialog: scriptDialog,
      updateField,
    })
    customActions.value = data._customActions || []
  }

  function updateField(fieldname: string, value: unknown, callback = () => {}) {
    runAction(
      async () => {
        await updateTicket(ticketId.value, { [fieldname]: value })
        ticket.fetch()
      },
      { success: __('Ticket updated successfully.'), fallback: __('Could not update this ticket') },
    )
    callback()
  }

  watch(ticketId, (name) => name && ticket.fetch(), { immediate: true })

  const feedback = useTicketFeedback(ticket)
  const thread = useTicketThread(ticket)
  const isClosed = computed(() => isClosedStatus(ticket.data?.status))
  const isUpdatingStatus = ref(false)

  const relatedArticles = createResource({
    url: 'helpdesk.api.article.get_related',
    makeParams: () => ({ query: ticket.data?.subject }),
  })
  watch(
    () => ticket.data?.subject,
    (subject) => subject && relatedArticles.fetch(),
    { immediate: true },
  )

  // The article pages are the desk's, under its `/helpdesk` router base.
  const suggestedArticles = computed(() =>
    (relatedArticles.data || []).map((article) => ({
      ...article,
      url: `/helpdesk/kb-public/articles/${article.name}`,
    })),
  )

  // Empty hides the button; as on the desk portal, any open ticket can be closed.
  const pageActionLabel = computed(() => {
    if (!isClosed.value) return __('Close')
    return settings.canCreateTicket.value ? __('Raise a ticket') : ''
  })

  const canRate = computed(() => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback)

  // Where a rating is required the status cannot be written without it.
  const wantsFeedback = computed(() => canRate.value && Boolean(config.value?.is_feedback_mandatory))

  function onPageAction() {
    if (isClosed.value) return navigateTo(ROUTES.newTicket)
    if (wantsFeedback.value) return feedback.openFeedback()
    askConfirm({
      title: __('Close ticket'),
      message: __('Are you sure you want to close this ticket?'),
      label: __('Close'),
      theme: 'red',
      action: closeTicket,
    })
  }

  function closeTicket() {
    return setStatus(CLOSED_STATUS, { fallback: __('Could not close this ticket') })
  }

  function setStatus(status: string, messages: { success?: string; fallback: string }) {
    return runAction(
      async () => {
        await updateTicket(ticketId.value, { status })
        ticket.fetch()
      },
      { busy: isUpdatingStatus, ...messages },
    )
  }

  return {
    ...settings,
    ...thread,
    ...useTicketDetails(ticket, thread),
    ...useReplyComposer(ticket),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    ticketId,
    ticket,
    customActions,
    pageActionLabel,
    pageActionIcon: computed(() => (isClosed.value ? 'lucide-plus' : 'lucide-check')),
    onPageAction,
    suggestedArticles,
    openHelpArticle: (article) => (window.location.href = article.url),
  }
}
