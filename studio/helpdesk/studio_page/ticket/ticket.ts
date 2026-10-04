import { computed, markRaw, ref, watch } from 'vue'
import { createResource, dayjs, dayjsLocal } from 'frappe-ui'
import LucideCircleCheck from '~icons/lucide/circle-check'
import LucideStar from '~icons/lucide/star'
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
import {
  CLOSED_STATUS,
  isClosedStatus,
  isResolvedStatus,
  loadTicketMeta,
} from '@app/stores/ticketMeta'
import { DATE_FORMATS, runAction, updateTicket } from '@app/utils'

// Fallback for `confirm_resolution_after_days`; HD Settings owns the real value.
const RESOLVED_PROMPT_DAYS = 5
const POPULAR_ARTICLE_LIMIT = 3
const REOPENED_STATUS = 'Open'

export default function setup(context) {
  const { route } = context
  const settings = useSettingsModal(context)
  const { config } = settings
  // The composer shows the reader's own avatar, which rides on the settings payload.
  settings.loadSettings()
  loadTicketMeta()

  const ticketId = computed(() => String(route?.params?.name || ''))

  const ticket = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_one',
    makeParams: () => ({ name: ticketId.value }),
  })

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
    rated: __('Rated'),
  }))

  // Closing and rating happen on the ticket, not in a message; HD Ticket's history dates them.
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
    const rating = thread.rating.value
    if (!rating) return closings
    // A rating from before the history was kept falls back to the resolution date.
    const at = ratingChange.value?.on || ticket.data?.resolution_date
    return [...closings, { type: 'feedback', key: 'feedback', timestamp: at, icon: markRaw(LucideStar), data: {} }]
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

  const popularArticles = createResource({
    url: 'helpdesk.api.knowledge_base.get_public_articles',
    method: 'GET',
    params: { limit: POPULAR_ARTICLE_LIMIT, sort: 'popular' },
  })

  const isRelated = computed(() => Boolean(relatedArticles.data?.length))

  const suggestedArticles = computed(
    () => (isRelated.value ? relatedArticles.data : popularArticles.data) || [],
  )

  const suggestedHeading = computed(() =>
    __(isRelated.value ? 'Related help' : 'Popular help'),
  )

  // Empty hides the button: a customer may close only what support has resolved.
  const pageActionLabel = computed(() => (isResolved.value ? __('Close') : ''))

  const canCreateTicket = computed(() => settings.canCreateTicket.value && isClosed.value)

  const canRate = computed(() => Boolean(thread.lastAgentReply.value) && !ticket.data?.feedback)

  // Where a rating is required the status cannot be written without it.
  const wantsFeedback = computed(() => canRate.value && Boolean(config.value?.is_feedback_mandatory))

  // Asked once, under the latest agent reply, and only after the resolution has stood a while.
  const solvePromptAt = computed(() => {
    const data = ticket.data
    if (!data || !isResolved.value) return null
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
    const resolvedOn = ticket.data?.resolution_date
    return Boolean(resolvedOn) && dayjs().diff(dayjs(resolvedOn), 'day') >= days
  }

  // The prompt is a row of its own, drawn by the timeline's `item-solve_prompt` slot.
  // The chat layout's own rows for the same two events, merged with its bubbles by time.
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
    // The close the rating answers heads the footer, so it is not drawn twice.
    const closing = rows.findLast(
      (row) => row.kind === 'closed' && dayjs(row.creation).valueOf() <= dayjs(rating.creation).valueOf(),
    )
    const stars = Math.round(thread.rating.value?.rating || 0)
    Object.assign(rating, {
      closedLine: closing ? `${closing.text} · ${closing.clock}` : '',
      tags: (thread.rating.value?.tags || []).map((tag) => tag.label).join(' · '),
      ratedLine: __('{0} rated {1} of 5', [ratedBy.value, stars]),
    })
    return rows.filter((row) => row !== closing)
  })
  const chatRows = computed(() => {
    const rows = [...thread.conversation.value, ...chatEvents.value].sort(
      (first, second) => dayjs(first.creation).valueOf() - dayjs(second.creation).valueOf(),
    )
    // A bubble's gap was set for the bubble after it; an event below it gets the full gap.
    return rows.map((row, index) =>
      !row.kind && rows[index + 1]?.kind ? { ...row, rowSpacing: ROW_GAP } : row,
    )
  })

  const timeline = computed(() =>
    [...thread.activities.value, ...timelineEvents.value].sort(
      (first, second) => dayjs(first.timestamp).valueOf() - dayjs(second.timestamp).valueOf(),
    ),
  )

  const activities = computed(() =>
    timeline.value.flatMap((activity) =>
      activity.key === solvePromptAt.value
        ? [activity, { type: 'solve_prompt', key: 'solve-prompt', timestamp: activity.timestamp, data: {} }]
        : [activity],
    ),
  )

  // Where a rating is still owed, the dialog's save is the only way past `validate_feedback`.
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
    ...thread,
    drawer: useDrawer(context.route),
    ...useTicketDetails(ticket, thread),
    ...useReplyComposer(ticket),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    words,
    ticketId,
    ticket,
    activities,
    isChat: thread.isChat,
    conversation: chatRows,
    solvePromptAt,
    ratedBy,
    // The timeline's own clock, so it reads the same as the rows around it.
    ratedTimeAgo: computed(() => {
      const at = ratingChange.value?.on || ticket.data?.resolution_date
      return at ? dayjsLocal(at).fromNow() : ''
    }),
    canCreateTicket,
    pageActionLabel,
    pageActionIcon: 'check',
    onPageAction,
    confirmSolved,
    reopenTicket,
    suggestedArticles,
    suggestedHeading,
    openHelpArticle: (article) => navigateTo(ROUTES.article(article.name)),
  }
}
