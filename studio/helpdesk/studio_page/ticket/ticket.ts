import { computed, markRaw, ref, watch } from 'vue'
import { createResource, dayjs, toast } from 'frappe-ui'
import LucideCircleCheck from '~icons/lucide/circle-check'
import { createToast, setupCustomizations } from '@helpdesk/shared/formScripts'
import { __ } from '@helpdesk/shared/translation'
import { useDrawer } from '@app/composables/useDrawer'
import { useOutsideHoursBanner } from '@app/composables/useOutsideHoursBanner'
import { useReplyComposer } from '@app/composables/useReplyComposer'
import { useTicketDetails } from '@app/composables/useTicketDetails'
import { useTicketFeedback } from '@app/composables/useTicketFeedback'
import { useTicketThread } from '@app/composables/useTicketThread'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { CLOSED_STATUS, isClosedStatus, isResolvedStatus, loadTicketMeta } from '@app/stores/ticketMeta'
import { askConfirm, runAction, scriptDialog, updateTicket } from '@app/utils'

// Used when HD Settings has no `confirm_resolution_after_days`.
const RESOLVED_PROMPT_DAYS = 5
const REOPENED_STATUS = 'Open'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer shows the reader's avatar, which comes with the settings payload.
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
  const isResolved = computed(() => isResolvedStatus(ticket.data?.status))
  const isUpdatingStatus = ref(false)

  // Closing changes the ticket, not the thread, so its date comes from the ticket's history.
  const timelineChanges = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_timeline_changes',
    method: 'GET',
    makeParams: () => ({ name: ticketId.value }),
  })
  watch(
    () => ticket.data?.modified,
    (modified) => modified && timelineChanges.fetch(),
    { immediate: true },
  )

  const timelineEvents = computed(() =>
    (timelineChanges.data || [])
      .filter((change) => change.field === 'status' && isClosedStatus(change.to))
      .map((change) => ({
        type: 'log',
        key: `closed:${change.on}`,
        timestamp: change.on,
        author: { fullname: change.by.name, image: change.by.image },
        icon: markRaw(LucideCircleCheck),
        data: { name: `closed:${change.on}`, subtype: 'info', text: __('{0} closed the ticket', [change.by.name]) },
      })),
  )

  const relatedArticles = createResource({
    url: 'helpdesk.api.article.get_related',
    makeParams: () => ({ query: ticket.data?.subject }),
  })
  watch(
    () => ticket.data?.subject,
    (subject) => subject && relatedArticles.fetch(),
    { immediate: true },
  )

  const suggestedArticles = computed(() => relatedArticles.data || [])

  const canRate = computed(() => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback)
  // Where a rating is required, the status cannot be written without it.
  const wantsFeedback = computed(() => canRate.value && Boolean(config.value?.is_feedback_mandatory))

  const promptAfterDays = computed(() => Number(config.value?.confirm_resolution_after_days ?? RESOLVED_PROMPT_DAYS))

  // Asked once, of the requester, under the latest agent reply, once the resolution has stood a while.
  // It takes the reply's time, and the thread puts the page's rows after emails at the same time.
  const solvePrompt = computed(() => {
    const data = ticket.data
    const reply = thread.lastAgentReply.value
    if (!data || !reply || !isResolved.value || !data.resolution_date) return null
    if (dayjs().diff(dayjs(data.resolution_date), 'day') < promptAfterDays.value) return null
    const viewer = config.value?.session_user
    if (viewer && data.raised_by && viewer !== data.raised_by) return null
    return { type: 'solve_prompt', key: 'solve-prompt', timestamp: reply.communication_date || reply.creation, data: {} }
  })

  const threadExtras = computed(() => [...timelineEvents.value, ...(solvePrompt.value ? [solvePrompt.value] : [])])

  // Where a rating is still owed, the feedback dialog is the only way past `validate_feedback`.
  function confirmSolved() {
    if (canRate.value) return feedback.openFeedback()
    return closeTicket()
  }

  // An agent reply leaves the ticket "Replied", so No puts it back in the queue.
  function reopenTicket() {
    return setStatus(REOPENED_STATUS, {
      success: __('Reopened, we will take another look'),
      fallback: __('Could not reopen this ticket'),
    })
  }

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
    ...useTicketDetails(ticket, thread),
    ...useReplyComposer(ticket),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    drawer: useDrawer(route),
    ticketId,
    ticket,
    rating: thread.rating,
    threadExtras,
    customActions,
    // Empty hides the header button; any open ticket can be closed, a closed one leads to a new ticket.
    pageActionLabel: computed(() => {
      if (!isClosed.value) return __('Close')
      return settings.canCreateTicket.value ? __('Raise a ticket') : ''
    }),
    pageActionIcon: computed(() => (isClosed.value ? 'lucide-plus' : 'lucide-check')),
    onPageAction,
    confirmSolved,
    reopenTicket,
    suggestedArticles,
    openHelpArticle: (article) => navigateTo(ROUTES.article(article.name)),
  }
}
