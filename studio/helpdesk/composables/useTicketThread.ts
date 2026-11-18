import { computed } from 'vue'

export function useTicketThread(ticket) {
  // By role, not direction: agents may reply from the portal. Skip the request itself.
  // Not `first_responded_on`: that is stamped on a status change.
  const firstAgentReply = computed(() => (ticket.data?.communications || []).slice(1).find((message) => message.is_agent) || null)

  const rating = computed(() => {
    const data = ticket.data
    if (!data?.feedback_rating) return null
    return {
      // HD Ticket stores a fraction; Rating counts stars.
      rating: data.feedback_rating * 5,
      feedback: data.feedback || '',
      comment: data.feedback_extra || '',
    }
  })

  return {
    rating,
    firstAgentReply,
  }
}
