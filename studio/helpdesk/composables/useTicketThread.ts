import { computed, watch } from 'vue'
import { dayjs } from 'frappe-ui'
import { timeAgo } from '@helpdesk/shared/utils'
import { usePreferences } from '@app/stores/preferences'
import { layoutOf, GROUP_SECONDS, GROUPED_GAP, ROW_GAP } from '@app/composables/messageLayout'
import { DATE_FORMATS } from '@app/utils'

// Waits for the email frames to size themselves, which happens after paint.
const SCROLL_TO_MESSAGE_MS = 1000

export function useTicketThread(ticket) {
  const { conversationLayout } = usePreferences()
  const isChat = computed(() => conversationLayout.value === 'chat')

  const conversation = computed(() => {
    const rows = sortByCreation().map(toMessageRow)
    rows.forEach((row, index) => {
      const last = index === rows.length - 1
      row.railHeight = isChat.value ? '0px' : last ? '20px' : '100%'
      const opens = !continues(rows[index - 1], row)
      row.insideByline = !isChat.value
      row.outsideByline = isChat.value && opens
      row.showAvatar = !isChat.value || opens
    })
    rows.forEach((row, index) => {
      const next = rows[index + 1]
      row.rowSpacing = next && isChat.value && !next.outsideByline ? GROUPED_GAP : ROW_GAP
    })
    return rows
  })

  function continues(previous, row) {
    if (!previous) return false
    return (
      previous.isAgentReply === row.isAgentReply &&
      previous.sender === row.sender &&
      dayjs(row.creation).diff(dayjs(previous.creation), 's') <= GROUP_SECONDS
    )
  }

  let hasScrolledToMessage = false
  watch(conversation, (messages) => {
    if (hasScrolledToMessage || !messages.length) return
    hasScrolledToMessage = true
    const id = location.hash.slice(1) || messages[messages.length - 1].name
    setTimeout(
      () => document.getElementById(id)?.scrollIntoView({ block: 'nearest' }),
      SCROLL_TO_MESSAGE_MS,
    )
  })

  function sortByCreation() {
    return [...(ticket.data?.communications || [])].sort(
      (first, second) => new Date(first.creation).getTime() - new Date(second.creation).getTime(),
    )
  }

  function toMessageRow(message) {
    return {
      name: message.name,
      content: message.content,
      sender: message.user?.name || message.sender,
      image: message.user?.image,
      creation: message.creation,
      timeAgo: timeAgo(message.creation),
      clock: clockTime(message.creation),
      fullDate: dayjs(message.creation).format(DATE_FORMATS.tooltip),
      attachments: message.attachments || [],
      // Frappe's direction, not identities: `sender` is an email, `raised_by` may not be.
      isAgentReply: message.sent_or_received === 'Sent',
      isChat: isChat.value,
      railHeight: '100%',
      ...layoutOf(isChat.value, message.sent_or_received !== 'Sent'),
    }
  }

  const lastAgentReply = computed(
    () => [...conversation.value].reverse().find((row) => row.isAgentReply) || null,
  )

  // Not `first_responded_on`: that is stamped on a status transition, so it lies both ways.
  const firstAgentReply = computed(
    () => conversation.value.find((row) => row.isAgentReply) || null,
  )

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

  function clockTime(value: string) {
    const at = dayjs(value)
    const time = at.format(DATE_FORMATS.clock)
    if (at.isSame(dayjs(), 'day')) return time
    const day = at.isSame(dayjs(), 'year') ? DATE_FORMATS.day : DATE_FORMATS.dayWithYear
    return `${at.format(day)} at ${time}`
  }

  return {
    rating,
    lastAgentReply,
    firstAgentReply,
    conversation,
  }
}
