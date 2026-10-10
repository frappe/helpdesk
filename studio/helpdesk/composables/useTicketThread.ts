import { computed } from 'vue'
import { dayjsLocal } from 'frappe-ui'
import { timeAgo } from '@helpdesk/shared/utils'
import { DATE_FORMATS } from '@app/utils'

export function useTicketThread(ticket) {
  // Oldest first, the order ActivityTimeline keeps in the DOM.
  const messages = computed(() => ticket.data?.communications || [])

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
      fullDate: dayjsLocal(when).format(DATE_FORMATS.tooltip),
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
    lastAgentReply,
    firstAgentReply,
    activities,
  }
}
