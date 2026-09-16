import { computed, watch } from 'vue'
import { call, createResource, dayjs, toast } from 'frappe-ui'
import { useSettingsModal } from '@app/stores/settings'
import { useTicketThread } from '@app/stores/ticket/thread'
import { useTicketDetails } from '@app/stores/ticket/details'
import { useTicketFeedback } from '@app/stores/ticket/feedback'
import { loadTicketMeta } from '@app/components/list/ticketCells'

// The page is drawn from Studio blocks, so this returns display-ready state and actions.
// Fallback for `confirm_resolution_after_days`; HD Settings owns the real value.
const RESOLVED_PROMPT_DAYS = 5

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer shows the reader's own avatar, which rides on the settings payload.
  settings.loadSettings()
  // On mount, not at import: a signed-out visitor cannot call it.
  loadTicketMeta()

  const ticketId = computed(() => String(route?.params?.name || ''))

  // Answers with the communications too, so the thread costs no second request.
  const ticket = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_one',
    makeParams: () => ({ name: ticketId.value }),
  })

  watch(ticketId, (name) => name && ticket.fetch(), { immediate: true })

  const feedback = useTicketFeedback(ticket)
  const thread = useTicketThread(ticket)

  // Empty hides the button. Resolved keeps its Close: support is done, the customer may not be.
  const pageActionLabel = computed(() =>
    ticket.data && ticket.data.status !== 'Closed' ? 'Close' : '',
  )

  // A ticket still in flight already has a place to say more, and it is this thread.
  const canCreateTicket = computed(
    () => settings.canCreateTicket.value && ticket.data?.status === 'Closed',
  )

  // Nothing to rate until someone answers, and a rating already given is never asked again.
  const canRate = computed(
    () => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback,
  )

  // Where a rating is required the status cannot be written without it.
  const wantsFeedback = computed(
    () => canRate.value && Boolean(config.value?.is_feedback_mandatory),
  )

  // Asked once, under the latest agent reply, and only after the resolution has stood a while.
  const solvePromptAt = computed(() => {
    const data = ticket.data
    if (!data || data.status !== 'Resolved') return null
    if (!settledFor(promptAfterDays.value)) return null
    const viewer = config.value?.session_user
    if (viewer && data.raised_by && viewer !== data.raised_by) return null
    return thread.lastAgentReply.value?.name || null
  })

  // A Single omits a field it was never given, so a missing key falls back, not to zero.
  const promptAfterDays = computed(() => {
    const days = config.value?.confirm_resolution_after_days
    return days === undefined || days === null ? RESOLVED_PROMPT_DAYS : Number(days)
  })

  function settledFor(days: number) {
    const on = ticket.data?.resolution_date
    return Boolean(on) && dayjs().diff(dayjs(on), 'day') >= days
  }

  // Where a rating is still owed, the dialog's save is the only way past `validate_feedback`.
  async function confirmSolved() {
    if (canRate.value) return feedback.openFeedback('Closed')
    return closeTicket()
  }

  // An agent reply leaves the ticket "Replied", so No puts it back in the queue.
  async function reopenTicket() {
    try {
      await call('frappe.client.set_value', {
        doctype: 'HD Ticket',
        name: ticketId.value,
        fieldname: 'status',
        value: 'Open',
      })
      ticket.fetch()
      toast.success('Reopened — we will take another look')
    } catch (error) {
      toast.error(error?.messages?.[0] || 'Could not reopen this ticket')
    }
  }

  function onPageAction() {
    if (wantsFeedback.value) return feedback.openFeedback()
    settings.askConfirm({
      title: 'Close ticket',
      message: 'Are you sure you want to close this ticket?',
      label: 'Close',
      action: closeTicket,
    })
  }

  async function closeTicket() {
    try {
      await call('frappe.client.set_value', {
        doctype: 'HD Ticket',
        name: ticketId.value,
        fieldname: 'status',
        value: 'Closed',
      })
      ticket.fetch()
    } catch (error) {
      toast.error(error?.messages?.[0] || 'Could not close this ticket')
    }
  }

  return {

    ...settings,
    ...thread,
    ...useTicketDetails(ticket, thread),
    ...feedback,
    ticketId,
    ticket,
    canCreateTicket,
    pageActionLabel,
    pageActionIcon: 'check',
    onPageAction,
    solvePromptAt,
    confirmSolved,
    reopenTicket,
  }
}
