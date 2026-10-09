import { computed } from 'vue'

export function useTicketThread(ticket) {
  // By the author's role, not direction: an agent may reply from the portal.
  // The first message is the request itself, even when an agent raised it.
  const agentReplies = computed(() => (ticket.data?.communications || []).slice(1).filter((message) => message.is_agent))
  const lastAgentReply = computed(() => agentReplies.value.at(-1) || null)
  // Not `first_responded_on`: that is stamped on a status transition, not on the reply.
  const firstAgentReply = computed(() => agentReplies.value[0] || null)

  const rating = computed(() => {
    const data = ticket.data
    if (!data?.feedback_rating) return null
    return {
      // HD Ticket stores a fraction; the Rating component counts stars.
      rating: data.feedback_rating * 5,
      feedback: data.feedback || '',
      comment: data.feedback_extra || '',
    }
  })

  return {
    rating,
    lastAgentReply,
    firstAgentReply,
  }
}
