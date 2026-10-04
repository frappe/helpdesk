import { computed, watch } from 'vue'
import { dayjs } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { usePreferences } from '@app/stores/preferences'
import { useSession } from '@app/stores/session'
import { bubbleLayout, GROUP_SECONDS, GROUPED_GAP, ROW_GAP } from '@app/composables/messageLayout'
import { DATE_FORMATS } from '@app/utils'

// Waits for the email frames to size themselves, which happens after paint.
const SCROLL_TO_MESSAGE_MS = 1000

export function useTicketThread(ticket) {
  const { conversationLayout } = usePreferences()
  const { isPhone } = useSession()
  const isChat = computed(() => conversationLayout.value === 'chat')

  const messages = computed(() =>
    [...(ticket.data?.communications || [])]
      .sort((first, second) => new Date(first.creation).getTime() - new Date(second.creation).getTime())
      .map((message) => ({
        name: message.name,
        content: message.content,
        creation: message.creation,
        sender: message.user?.name || message.sender,
        email: message.sender,
        image: message.user?.image,
        attachments: message.attachments || [],
        // `sender` is an email and `raised_by` may not be, so direction is the only reliable side.
        isAgentReply: message.sent_or_received === 'Sent',
      })),
  )

  const activities = computed(() =>
    messages.value.map((message) => ({
      type: 'email',
      key: message.name,
      timestamp: message.creation,
      author: { fullname: message.sender, image: message.image, email: message.email },
      data: message,
    })),
  )

  const conversation = computed(() => {
    if (!isChat.value) return []
    const rows = messages.value.map((message) => ({
      ...message,
      clock: clockTime(message.creation),
      fullDate: dayjs(message.creation).format(DATE_FORMATS.tooltip),
      ...bubbleLayout(!message.isAgentReply, isPhone.value),
    }))
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

  function continues(previous, row) {
    return (
      Boolean(previous) &&
      previous.isAgentReply === row.isAgentReply &&
      previous.sender === row.sender &&
      dayjs(row.creation).diff(dayjs(previous.creation), 's') <= GROUP_SECONDS
    )
  }

  function clockTime(value: string) {
    const at = dayjs(value)
    const time = at.format(DATE_FORMATS.clock)
    if (at.isSame(dayjs(), 'day')) return time
    const day = at.format(at.isSame(dayjs(), 'year') ? DATE_FORMATS.day : DATE_FORMATS.dayWithYear)
    return __('{0} at {1}', [day, time])
  }

  // ActivityTimeline opens on the newest row itself; the chat Repeater has to be scrolled there.
  let hasScrolledToMessage = false
  watch(conversation, (rows) => {
    if (hasScrolledToMessage || !rows.length) return
    hasScrolledToMessage = true
    const id = location.hash.slice(1) || rows.at(-1).name
    setTimeout(() => document.getElementById(id)?.scrollIntoView({ block: 'nearest' }), SCROLL_TO_MESSAGE_MS)
  })

  const agentReplies = computed(() => messages.value.filter((message) => message.isAgentReply))
  const lastAgentReply = computed(() => agentReplies.value.at(-1) || null)
  // Not `first_responded_on`: that is stamped on a status transition, not on the reply.
  const firstAgentReply = computed(() => agentReplies.value[0] || null)

  const rating = computed(() => {
    const data = ticket.data
    if (!data?.feedback_rating) return null
    return {
      // HD Ticket stores a fraction; the Rating component counts stars.
      rating: data.feedback_rating * 5,
      tags: feedbackTags(data.feedback),
      comment: data.feedback_extra ? `“${data.feedback_extra}”` : '',
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
    isChat,
    activities,
    conversation,
    rating,
    clockTime,
    lastAgentReply,
    firstAgentReply,
  }
}
