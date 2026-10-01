import { computed, ref, watch } from 'vue'
import { createListResource, createResource, dayjs } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { useOutsideHoursBanner } from '@app/composables/useOutsideHoursBanner'
import { useReplyComposer } from '@app/composables/useReplyComposer'
import { useTicketDetails } from '@app/composables/useTicketDetails'
import { useTicketFeedback } from '@app/composables/useTicketFeedback'
import { useTicketThread } from '@app/composables/useTicketThread'
import { useSettingsModal } from '@app/stores/settings'
import {
  CLOSED_STATUS,
  isClosedStatus,
  isResolvedStatus,
  loadTicketMeta,
} from '@app/stores/ticketMeta'
import { runAction, updateTicket } from '@app/utils'

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
    feedbackTitle: __('Feedback Rating'),
  }))

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

  const popularArticles = createListResource({
    doctype: 'HD Article',
    filters: { status: 'Published' },
    fields: ['name', 'title'],
    orderBy: 'views desc',
    pageLength: POPULAR_ARTICLE_LIMIT,
  })

  const isRelated = computed(() => Boolean(relatedArticles.data?.length))

  // The article pages are the desk's, under its `/helpdesk` router base.
  const suggestedArticles = computed(() =>
    ((isRelated.value ? relatedArticles.data : popularArticles.data) || []).map((article) => ({
      ...article,
      url: `/helpdesk/kb-public/articles/${article.name}`,
    })),
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
  const activities = computed(() =>
    thread.activities.value.flatMap((activity) =>
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
    ...useTicketDetails(ticket, thread),
    ...useReplyComposer(ticket),
    ...useOutsideHoursBanner(ticket),
    ...feedback,
    words,
    ticketId,
    ticket,
    activities,
    isChat: thread.isChat,
    conversation: thread.conversation,
    solvePromptAt,
    canCreateTicket,
    pageActionLabel,
    pageActionIcon: 'check',
    onPageAction,
    confirmSolved,
    reopenTicket,
    suggestedArticles,
    suggestedHeading,
    openHelpArticle: (article) => (window.location.href = article.url),
  }
}
