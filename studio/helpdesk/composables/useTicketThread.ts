import { computed, watch } from 'vue'
import { dayjs } from 'frappe-ui'
import { timeAgo } from '@helpdesk/shared/utils'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'
import { bubbleLayout, GROUP_SECONDS, GROUPED_GAP, ROW_GAP } from '@app/composables/messageLayout'
import { DATE_FORMATS } from '@app/utils'

// Waits for the email frames to size themselves, which happens after paint.
const SCROLL_TO_MESSAGE_MS = 1000

export function useTicketThread(ticket) {
  // Oldest first, the order ActivityTimeline keeps in the DOM.
  const messages = computed(() =>
    [...(ticket.data?.communications || [])].sort(
      (first, second) => new Date(first.creation).getTime() - new Date(second.creation).getTime(),
    ),
  )

  const activities = computed(() => messages.value.map(toEmailActivity))

  function toEmailActivity(message) {
    const sender = message.user?.name || message.sender
    return {
      type: 'email',
      key: message.name,
      timestamp: message.creation,
      author: { fullname: sender, image: message.user?.image, email: message.sender },
      data: {
        name: message.name,
        sender,
        content: message.content,
        attachments: message.attachments || [],
      },
    }
  }

  // The chat layout is a Repeater of bubbles; the timeline layout is ActivityTimeline.
  const { conversationLayout } = usePreferences()
  const isChat = computed(() => conversationLayout.value === 'chat')
  const { isPhone } = useSession()

  const conversation = computed(() => {
    if (!isChat.value) return []
    const rows = messages.value.map(toBubble)
    rows.forEach((row, index) => {
      const opens = !continues(rows[index - 1], row)
      row.outsideByline = opens
      row.showAvatar = opens
    })
    rows.forEach((row, index) => {
      const next = rows[index + 1]
      row.rowSpacing = next && !next.outsideByline ? GROUPED_GAP : ROW_GAP
    })
    return rows
  })

  function toBubble(message) {
    return {
      name: message.name,
      content: message.content,
      sender: message.user?.name || message.sender,
      image: message.user?.image,
      creation: message.creation,
      clock: clockTime(message.creation),
      fullDate: dayjs(message.creation).format(DATE_FORMATS.tooltip),
      attachments: message.attachments || [],
      isAgentReply: message.sent_or_received === 'Sent',
      ...bubbleLayout(message.sent_or_received !== 'Sent', isPhone.value),
    }
  }

  function continues(previous, row) {
    if (!previous) return false
    return (
      previous.isAgentReply === row.isAgentReply &&
      previous.sender === row.sender &&
      dayjs(row.creation).diff(dayjs(previous.creation), 's') <= GROUP_SECONDS
    )
  }

  function clockTime(value: string) {
    const at = dayjs(value)
    const time = at.format(DATE_FORMATS.clock)
    if (at.isSame(dayjs(), 'day')) return time
    const day = at.isSame(dayjs(), 'year') ? DATE_FORMATS.day : DATE_FORMATS.dayWithYear
    return `${at.format(day)} at ${time}`
  }

  // ActivityTimeline opens on the newest row itself; the Repeater has to be scrolled there.
  let hasScrolledToMessage = false
  watch(conversation, (rows) => {
    if (hasScrolledToMessage || !rows.length) return
    hasScrolledToMessage = true
    const id = location.hash.slice(1) || rows[rows.length - 1].name
    setTimeout(
      () => document.getElementById(id)?.scrollIntoView({ block: 'nearest' }),
      SCROLL_TO_MESSAGE_MS,
    )
  })

  // Frappe's direction, not identities: `sender` is an email, `raised_by` may not be.
  const agentReplies = computed(() =>
    messages.value.filter((message) => message.sent_or_received === 'Sent'),
  )
  const lastAgentReply = computed(() => agentReplies.value.at(-1) || null)
  // Not `first_responded_on`: that is stamped on a status transition, so it lies both ways.
  const firstAgentReply = computed(() => agentReplies.value[0] || null)

  // Dated from `resolution_date`: HD Ticket stamps no time of its own for feedback.
  const rating = computed(() => {
    const data = ticket.data
    if (!data?.feedback_rating) return null
    const when = data.resolution_date || data.modified
    return {
      name: 'feedback',
      // HD Ticket stores the rating as a fraction; the Rating component counts stars.
      rating: data.feedback_rating * 5,
      tags: feedbackTags(data.feedback),
      comment: data.feedback_extra ? `“${data.feedback_extra}”` : '',
      timeAgo: timeAgo(when),
      fullDate: dayjs(when).format(DATE_FORMATS.tooltip),
    }
  })

  function feedbackTags(feedback: string) {
    return (feedback || '')
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => ({ label: part.charAt(0).toUpperCase() + part.slice(1) }))
  }

  return {
    rating,
    clockTime,
    lastAgentReply,
    firstAgentReply,
    activities,
    isChat,
    conversation,
  }
}
