import { computed, markRaw, onScopeDispose, ref, watch } from 'vue'
import { useDocumentVisibility } from '@vueuse/core'
import { createResource } from 'frappe-ui'
import { subscribeToDoc } from '@framework/ui/socket'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideRotateCcw from '~icons/lucide/rotate-ccw'
import { __ } from '@helpdesk/shared/translation'
import { useDrawer } from '@app/composables/useDrawer'
import { useOutsideHoursBanner } from '@app/composables/useOutsideHoursBanner'
import { useReplyComposer } from '@app/composables/useReplyComposer'
import { useTicketDetails } from '@app/composables/useTicketDetails'
import { useTicketFeedback } from '@app/composables/useTicketFeedback'
import { useTicketThread } from '@app/composables/useTicketThread'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { CLOSED_STATUS, isClosedStatus, loadTicketMeta } from '@app/stores/ticketMeta'
import { askConfirm, copyToClipboard, runAction, runFormScripts, updateTicket, type ActionOptions } from '@helpdesk/shared/utils'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer's avatar comes with the settings payload.
  settings.ensureSettings()
  loadTicketMeta()

  const ticketId = computed(() => String(route?.params?.name || ''))

  const customActions = ref([])

  const ticket = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_one',
    makeParams: () => ({ name: ticketId.value }),
  })
  // Only on a real change, or each script's calls would repeat.
  watch(
    () => ticket.data && `${ticket.data.name}:${ticket.data.modified}`,
    async (version) => {
      if (version) customActions.value = await runFormScripts(ticket.data, context, { doc: ticket.data, updateField })
    },
  )

  function saveTicket(values: Record<string, unknown>, options: ActionOptions) {
    return runAction(async () => {
      await updateTicket(ticketId.value, values)
      ticket.fetch()
    }, options)
  }

  function updateField(fieldname: string, value: unknown, callback = () => {}) {
    saveTicket(
      { [fieldname]: value },
      { success: __('Ticket updated successfully.'), fallback: __('Could not update this ticket') },
    )
    callback()
  }

  watch(ticketId, (name) => name && ticket.fetch(), { immediate: true })

  // Bursts, or pings mid-refetch, end in one trailing fetch.
  let refetchQueued = false
  function refresh() {
    if (!ticketId.value) return
    if (ticket.loading) refetchQueued = true
    else ticket.fetch()
  }
  watch(
    () => ticket.loading,
    (loading) => {
      if (loading || !refetchQueued) return
      refetchQueued = false
      ticket.fetch()
    },
  )

  // Customers aren't in the ticket's room; they get a ping on their own channel.
  watch(
    ticketId,
    (name, _, onCleanup) => name && onCleanup(subscribeToDoc(context.socket, 'HD Ticket', name)),
    { immediate: true },
  )
  function onTicketChange(payload) {
    const doc = payload?.doc || payload
    const doctype = doc?.reference_doctype || doc?.doctype
    const name = doc?.reference_name || doc?.name
    if (doctype === 'HD Ticket' && name === ticketId.value) refresh()
  }
  function onTicketPing(payload) {
    if (payload?.ticket_id === ticketId.value) refresh()
  }
  // Nothing replays events missed while disconnected or asleep.
  let wasDisconnected = false
  function onDisconnect() {
    wasDisconnected = true
  }
  function onConnect() {
    if (!wasDisconnected) return
    wasDisconnected = false
    refresh()
  }
  const listeners = {
    doc_update: onTicketChange,
    docinfo_update: onTicketChange,
    'helpdesk:ticket-update': onTicketPing,
    disconnect: onDisconnect,
    connect: onConnect,
  }
  for (const [event, handler] of Object.entries(listeners)) context.socket?.on(event, handler)
  // By handler: the socket is shared across pages.
  onScopeDispose(() => {
    for (const [event, handler] of Object.entries(listeners)) context.socket?.off(event, handler)
  })
  const visibility = useDocumentVisibility()
  watch(visibility, (state, before) => state === 'visible' && before === 'hidden' && refresh())

  const feedback = useTicketFeedback(saveTicket)
  const thread = useTicketThread(ticket)
  const isClosed = computed(() => isClosedStatus(ticket.data?.status))
  // As on the server: customers cannot touch closed or rated tickets.
  const isLocked = computed(() => isClosed.value || (!settings.isAgent.value && Boolean(ticket.data?.feedback)))
  const isUpdatingStatus = ref(false)

  // Close dates come from ticket history, not the thread.
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
  // Else the previous ticket's closes show until these arrive.
  watch(ticketId, () => timelineChanges.reset())

  const timelineEvents = computed(() =>
    (timelineChanges.data || [])
      .filter((change) => change.field === 'status' && isClosedStatus(change.to) !== isClosedStatus(change.from))
      .map((change) => {
        const closed = isClosedStatus(change.to)
        const key = `${closed ? 'closed' : 'reopened'}:${change.on}`
        const text = closed ? __('{0} closed the ticket', [change.by.name]) : __('{0} reopened the ticket', [change.by.name])
        const divider = closed ? __('Closed by {0}', [change.by.name]) : __('Reopened by {0}', [change.by.name])
        return {
          type: 'log',
          key,
          timestamp: change.on,
          author: { fullname: change.by.name, image: change.by.image },
          icon: markRaw(closed ? LucideCircleCheck : LucideRotateCcw),
          data: { name: key, subtype: 'info', text, divider },
        }
      }),
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

  // The server's test; it counts an agent reply that raised the ticket.
  // Email feedback sets only the rating, and a rating is final.
  const canRate = computed(
    () => Boolean(ticket.data?.has_agent_replied) && !ticket.data?.feedback && !ticket.data?.feedback_rating,
  )
  // As on the server: a required rating blocks the status write; agents exempt.
  const wantsFeedback = computed(
    () => canRate.value && Boolean(config.value?.is_feedback_mandatory) && !settings.isAgent.value,
  )

  function onPageAction() {
    if (isLocked.value) return navigateTo(ROUTES.newTicket({ from: 'closed-ticket' }))
    if (wantsFeedback.value) return feedback.openFeedback()
    askConfirm({
      title: __('Close ticket'),
      message: __('Are you sure you want to close this ticket?'),
      // Not "Close": the dialog's X is already named that.
      label: __('Close ticket'),
      theme: 'red',
      action: closeTicket,
    })
  }

  function closeTicket() {
    return saveTicket({ status: CLOSED_STATUS }, { busy: isUpdatingStatus, fallback: __('Could not close this ticket') })
  }

  return {
    ...settings,
    ...useTicketDetails(ticket, thread, timelineChanges),
    ...useReplyComposer(ticket, { ticketId, isClosed: isLocked, isAgent: settings.isAgent }),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    drawer: useDrawer(route),
    ticketId,
    ticket,
    rating: thread.rating,
    timelineEvents,
    customActions,
    // Empty hides the header button.
    pageActionLabel: computed(() => {
      if (!ticket.data) return ''
      if (!isLocked.value) return __('Close')
      return settings.canCreateTicket.value ? settings.raiseTicketLabel.value : ''
    }),
    pageActionIcon: computed(() => {
      if (!ticket.data) return ''
      return isLocked.value ? 'lucide-plus' : 'lucide-check'
    }),
    onPageAction,
    suggestedArticles,
    copyTicketId: () => copyToClipboard(ticket.data.name, __('Ticket #{0} copied', [ticket.data.name])),
  }
}
