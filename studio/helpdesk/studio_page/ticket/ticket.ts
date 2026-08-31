import { computed, watch } from 'vue'
import { call, createResource, dayjs, toast } from 'frappe-ui'
import { useSettingsModal } from '@app/stores/settings'
import { useTicketThread } from '@app/stores/ticketThread'
import { useTicketDetails } from '@app/stores/ticketDetails'
import { useTicketFeedback } from '@app/stores/ticketFeedback'
import { loadTicketMeta } from '@app/components/ticketCells'

// One ticket, read and replied to from the portal — the customer half of the agent
// portal's `desk/src/pages/ticket/TicketCustomer.vue`. The page is drawn entirely
// from Studio blocks, so this returns display-ready state and named actions: the
// blocks bind, they never compute.
// How long a resolution stands before the portal asks the requester to confirm it, when
// the helpdesk has not said. HD Settings owns the real value — see `confirm_resolution_after_days`.
const RESOLVED_PROMPT_DAYS = 5

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer shows the reader's own avatar, which rides on the settings payload.
  settings.loadSettings()
  // Status labels and colours for the summary's pill — the same list the ticket list reads,
  // fetched on mount rather than at import because a signed-out visitor cannot call it.
  loadTicketMeta()

  const ticketId = computed(() => String(route?.params?.name || ''))

  // The one call the agent portal makes: it answers with the communications, so the
  // thread costs no second request.
  const ticket = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_one',
    makeParams: () => ({ name: ticketId.value }),
  })

  watch(ticketId, (name) => name && ticket.fetch(), { immediate: true })

  const feedback = useTicketFeedback(ticket)
  const thread = useTicketThread(ticket)

  // The topbar carries the page's action, the way TicketCustomer keeps Close in its
  // LayoutHeader. Label and icon travel as data; the click calls `onPageAction`,
  // because a function does not survive a Studio prop binding. The header hides the
  // button on an empty label.
  //
  // Resolved keeps its Close: support believing a ticket is fixed is not the same as the
  // customer being done with it. Only a closed ticket has nowhere left to go — the same
  // line `check_update_perms` draws.
  const pageActionLabel = computed(() =>
    ticket.data && ticket.data.status !== 'Closed' ? 'Close' : '',
  )

  // The topbar's "Raise a ticket", narrowed for this page only — the shared header reads
  // whatever `canCreateTicket` the page hands it. A ticket still in flight already has a
  // place to say more, and it is this thread; once it is closed that door is shut, so
  // starting a new one becomes the thing to offer.
  const canCreateTicket = computed(
    () => settings.canCreateTicket.value && ticket.data?.status === 'Closed',
  )

  // Whether there is still a rating to ask for. Nothing to rate on a ticket nobody
  // answered — the same test as TicketCustomer's `showFeedback` — and nobody is asked
  // twice: a rating already given stands, and reopening a ticket does not clear it, so a
  // ticket that comes back and is fixed again settles without another dialog.
  const canRate = computed(
    () => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback,
  )

  // And whether the rating has to come first: where the helpdesk requires one, the status
  // cannot be written without it, so the dialog's save is the only way through.
  const wantsFeedback = computed(
    () => canRate.value && Boolean(config.value?.is_feedback_mandatory),
  )

  // "Did this solve it?", asked inline under the newest agent reply.
  //
  // Asked late, and only once: support marks the ticket Resolved, and if the requester has
  // not come back within five days the portal asks whether that was true. Before that the
  // ticket is either still moving or freshly answered, and asking then is nagging — the
  // reader can already say either thing by replying.
  //
  // Hung off the *latest* reply rather than repeated under every one: the question is about
  // where the conversation currently stands, and one live ask reads as a conversation while
  // N stacked ones read as nagging.
  //
  // Nobody but the person who raised it is asked, and a closed ticket is past asking.
  const solvePromptAt = computed(() => {
    const data = ticket.data
    if (!data || data.status !== 'Resolved') return null
    if (!settledFor(promptAfterDays.value)) return null
    const viewer = config.value?.session_user
    if (viewer && data.raised_by && viewer !== data.raised_by) return null
    // Which message is support's is the thread store's business — it owns the row shape
    // and the raiser-identity matching.
    return thread.lastAgentReply.value?.name || null
  })

  /** A helpdesk that wants to ask sooner, later, or straight away says so in HD Settings;
   *  a Single leaves a field it has never been given out of the payload entirely, so a
   *  missing key falls back rather than reading as zero. */
  const promptAfterDays = computed(() => {
    const days = config.value?.confirm_resolution_after_days
    return days === undefined || days === null ? RESOLVED_PROMPT_DAYS : Number(days)
  })

  /** Whether the resolution has stood unchallenged this long. `resolution_date` is stamped
   *  on entering the resolved category, so it is the moment the clock starts from. */
  function settledFor(days: number) {
    const on = ticket.data?.resolution_date
    return Boolean(on) && dayjs().diff(dayjs(on), 'day') >= days
  }

  // Yes ends the ticket: it has been resolved for days and the requester has now said so.
  // Where a rating is still owed the dialog carries the close, since its single save is the
  // only way past `validate_feedback` on a helpdesk that requires one.
  async function confirmSolved() {
    if (canRate.value) return feedback.openFeedback('Closed')
    return closeTicket()
  }

  // No is never a dead end: an agent reply usually leaves the ticket "Replied", so this
  // puts it back to Open and into the queue rather than just dismissing the question.
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
