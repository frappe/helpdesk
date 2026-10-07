import { computed } from 'vue'

export function useTicketThread(ticket) {
  // `sender` is an email and `raised_by` may not be, so direction is the only reliable side.
  const agentReplies = computed(() =>
    (ticket.data?.communications || []).filter((message) => message.sent_or_received === 'Sent'),
  )
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
    rating,
    lastAgentReply,
    firstAgentReply,
  }
}
