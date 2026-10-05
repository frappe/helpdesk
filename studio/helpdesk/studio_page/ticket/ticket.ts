import { computed, markRaw, ref, watch } from 'vue'
import { createResource, dayjs, dayjsLocal, toast } from 'frappe-ui'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideStar from '~icons/lucide/star'
import { createToast, setupCustomizations } from '@helpdesk/shared/formScripts'
import { __ } from '@helpdesk/shared/translation'
import { useDrawer } from '@app/composables/useDrawer'
import { useOutsideHoursBanner } from '@app/composables/useOutsideHoursBanner'
import { useReplyComposer } from '@app/composables/useReplyComposer'
import { useTicketDetails } from '@app/composables/useTicketDetails'
import { useTicketFeedback } from '@app/composables/useTicketFeedback'
import { useTicketThread } from '@app/composables/useTicketThread'
import { ROW_GAP } from '@app/composables/messageLayout'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { CLOSED_STATUS, isClosedStatus, isResolvedStatus, loadTicketMeta } from '@app/stores/ticketMeta'
import { DATE_FORMATS, runAction, scriptDialog, updateTicket } from '@app/utils'

// Used when HD Settings has no `confirm_resolution_after_days`.
const RESOLVED_PROMPT_DAYS = 5
const POPULAR_ARTICLE_LIMIT = 3
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

  const words = computed(() => ({
    ...settings.words.value,
    status: __('Status'),
    composerPrompt: __('Type a message'),
    solveAsk: __('Did this solve your issue?'),
    solveYes: __("Yes, it's fixed"),
    solveNo: __('No, still an issue'),
    ratingLabel: __('Rating'),
    ratedSupport: __('rated the support'),
  }))

  // Closing and rating change the ticket, not the thread, so their dates come from its history.
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

  const ratingChange = computed(() =>
    (timelineChanges.data || []).findLast((change) => change.field === 'feedback_rating' && change.to),
  )
  const ratedBy = computed(() => ratingChange.value?.by?.name || ticket.data?.raised_by || '')
  // A rating from before the history was kept falls back to the resolution date.
  const ratedAt = computed(() => ratingChange.value?.on || ticket.data?.resolution_date)

  const timelineEvents = computed(() => {
    const closings = (timelineChanges.data || [])
      .filter((change) => change.field === 'status' && isClosedStatus(change.to))
      .map((change) => ({
        type: 'log',
        key: `closed:${change.on}`,
        timestamp: change.on,
        author: { fullname: change.by.name, image: change.by.image },
        icon: markRaw(LucideCircleCheck),
        data: { name: `closed:${change.on}`, subtype: 'info', text: __('{0} closed the ticket', [change.by.name]) },
      }))
    if (!thread.rating.value) return closings
    return [
      ...closings,
      { type: 'feedback', key: 'feedback', timestamp: ratedAt.value, icon: markRaw(LucideStar), data: {} },
    ]
  })

  const popularArticles = createResource({
    url: 'helpdesk.api.knowledge_base.get_public_articles',
    method: 'GET',
    params: { limit: POPULAR_ARTICLE_LIMIT, sort: 'popular' },
  })

  const relatedArticles = createResource({
    url: 'helpdesk.api.article.get_related',
    makeParams: () => ({ query: ticket.data?.subject }),
    onSuccess: (data) => !data.length && popularArticles.fetch(),
    onError: () => popularArticles.fetch(),
  })
  watch(
    () => ticket.data?.subject,
    (subject) => subject && relatedArticles.fetch(),
    { immediate: true },
  )

  const isRelated = computed(() => Boolean(relatedArticles.data?.length))
  const suggestedArticles = computed(() => (isRelated.value ? relatedArticles.data : popularArticles.data) || [])
  const suggestedHeading = computed(() => (isRelated.value ? __('Related help') : __('Popular help')))

  const canRate = computed(() => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback)
  // Where a rating is required, the status cannot be written without it.
  const wantsFeedback = computed(() => canRate.value && Boolean(config.value?.is_feedback_mandatory))

  const promptAfterDays = computed(() => Number(config.value?.confirm_resolution_after_days ?? RESOLVED_PROMPT_DAYS))

  // Asked once, of the requester, under the latest agent reply, once the resolution has stood a while.
  const solvePromptAt = computed(() => {
    const data = ticket.data
    if (!data || !isResolved.value || !data.resolution_date) return null
    if (dayjs().diff(dayjs(data.resolution_date), 'day') < promptAfterDays.value) return null
    const viewer = config.value?.session_user
    if (viewer && data.raised_by && viewer !== data.raised_by) return null
    return thread.lastAgentReply.value?.name || null
  })

  const activities = computed(() =>
    byTime([...thread.activities.value, ...timelineEvents.value], 'timestamp').flatMap((activity) =>
      activity.key === solvePromptAt.value
        ? [activity, { type: 'solve_prompt', key: 'solve-prompt', timestamp: activity.timestamp, data: {} }]
        : [activity],
    ),
  )

  // The chat layout's rows for the same events, merged with its bubbles by time.
  const chatEvents = computed(() => {
    const rows = timelineEvents.value.map((event) => ({
      name: event.key,
      kind: event.type === 'log' ? 'closed' : 'rating',
      creation: event.timestamp,
      clock: event.timestamp ? thread.clockTime(event.timestamp) : '',
      fullDate: event.timestamp ? dayjs(event.timestamp).format(DATE_FORMATS.tooltip) : '',
      text: event.type === 'log' ? __('Closed by {0}', [event.author.fullname]) : '',
    }))
    const rating = rows.find((row) => row.kind === 'rating')
    if (!rating) return rows
    // The close the rating answers heads the rating card, so it is not drawn twice.
    const closing = rows.findLast(
      (row) => row.kind === 'closed' && dayjs(row.creation).valueOf() <= dayjs(rating.creation).valueOf(),
    )
    Object.assign(rating, {
      closedLine: closing ? `${closing.text} · ${closing.clock}` : '',
      tags: thread.rating.value.tags.map((tag) => tag.label).join(' · '),
      ratedLine: __('{0} rated {1} of 5', [ratedBy.value, Math.round(thread.rating.value.rating)]),
    })
    return rows.filter((row) => row !== closing)
  })

  const conversation = computed(() => {
    const rows = byTime([...thread.conversation.value, ...chatEvents.value], 'creation')
    // A bubble's gap was set for the bubble after it; an event below it gets the full gap.
    return rows.map((row, index) => (!row.kind && rows[index + 1]?.kind ? { ...row, rowSpacing: ROW_GAP } : row))
  })

  function byTime(rows, key: string) {
    return rows.sort((first, second) => dayjs(first[key]).valueOf() - dayjs(second[key]).valueOf())
  }

  // Where a rating is still owed, the feedback dialog is the only way past `validate_feedback`.
  function confirmSolved() {
    if (canRate.value) return feedback.openFeedback(CLOSED_STATUS)
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
    settings.askConfirm({
      title: __('Close ticket'),
      message: __('Are you sure you want to close this ticket?'),
      label: __('Close'),
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
    words,
    ticketId,
    ticket,
    isChat: thread.isChat,
    rating: thread.rating,
    activities,
    conversation,
    solvePromptAt,
    ratedBy,
    // dayjsLocal, the clock ActivityTimeline uses for the rows around it.
    ratedTimeAgo: computed(() => (ratedAt.value ? dayjsLocal(ratedAt.value).fromNow() : '')),
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
    suggestedHeading,
    openHelpArticle: (article) => navigateTo(ROUTES.article(article.name)),
  }
}
