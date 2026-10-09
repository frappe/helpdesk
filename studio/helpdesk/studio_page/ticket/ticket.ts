import { computed, markRaw, onScopeDispose, ref, watch } from 'vue'
import { useDocumentVisibility } from '@vueuse/core'
import { createResource, toast } from 'frappe-ui'
import { subscribeToDoc } from '@framework/ui/socket'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideRotateCcw from '~icons/lucide/rotate-ccw'
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
import { CLOSED_STATUS, isClosedStatus, loadTicketMeta } from '@app/stores/ticketMeta'
import { askConfirm, runAction, scriptDialog, updateTicket } from '@app/utils'

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

  // A burst of pings, or a ping during the page's own refetch, ends in one trailing fetch.
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

  // Agents hear the ticket's room; customers are kept out of it and get a bare ping on their own channel.
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
  // Nothing replays what was sent while the socket was down or the tab asleep.
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
  // By handler: the socket is shared, and a bare `off(event)` would drop other pages' listeners too.
  onScopeDispose(() => {
    for (const [event, handler] of Object.entries(listeners)) context.socket?.off(event, handler)
  })
  const visibility = useDocumentVisibility()
  watch(visibility, (state, before) => state === 'visible' && before === 'hidden' && refresh())

  const feedback = useTicketFeedback(ticket)
  const thread = useTicketThread(ticket)
  const isClosed = computed(() => isClosedStatus(ticket.data?.status))
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
  // Another ticket's closes would show until its own arrive.
  watch(ticketId, () => timelineChanges.reset())

  const timelineEvents = computed(() =>
    (timelineChanges.data || [])
      .filter((change) => change.field === 'status' && isClosedStatus(change.to) !== isClosedStatus(change.from))
      .map((change) => {
        const closed = isClosedStatus(change.to)
        const key = `${closed ? 'closed' : 'reopened'}:${change.on}`
        const text = closed ? __('{0} closed the ticket', [change.by.name]) : __('{0} reopened the ticket', [change.by.name])
        // The chat layout draws these as dividers, which read as a label rather than a sentence.
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

  const canRate = computed(() => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback)
  // Where a rating is required, the status cannot be written without it.
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
    ...useTicketDetails(ticket, thread, timelineChanges),
    ...useReplyComposer(ticket, config),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    drawer: useDrawer(route),
    ticketId,
    ticket,
    rating: thread.rating,
    timelineEvents,
    customActions,
    // Empty hides the header button; any open ticket can be closed, a closed one leads to a new ticket.
    pageActionLabel: computed(() => {
      if (!ticket.data) return ''
      if (!isClosed.value) return __('Close')
      return settings.canCreateTicket.value ? __('Raise a ticket') : ''
    }),
    pageActionIcon: computed(() => {
      if (!ticket.data) return ''
      return isClosed.value ? 'lucide-plus' : 'lucide-check'
    }),
    onPageAction,
    suggestedArticles,
    openHelpArticle: (article) => navigateTo(ROUTES.article(article)),
  }
}
