import { computed, ref, watch } from 'vue'
import { timeAgo } from '@app/utils'
import { createResource, dayjs } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { layoutOf, GROUP_SECONDS, GROUPED_GAP, ROW_GAP } from '@app/components/ticket/bubbleLayout'
import { useReplyComposer } from './composer'

// The message thread, the outside-working-hours banner and the reply composer —
// the data behind `desk/src/pages/ticket/TicketConversation.vue` and
// `TicketTextEditor.vue`. The page draws all of it from Studio blocks, so every
// value a block binds is finished here: no formatting is left to an expression.

const DATE_FORMAT = 'ddd, MMM D, YYYY h:mm A'
// Chat stamps the clock, the way every chat does: a message is a moment, not an age.
const CLOCK_FORMAT = 'h:mm A'
const DAY_FORMAT = 'D MMMM'
const YEAR_FORMAT = 'D MMMM YYYY'
export function useTicketThread(ticket) {
  const { conversationLayout } = usePreferences()
  const isChat = computed(() => conversationLayout.value === 'chat')

  const conversation = computed(() => {
    const rows = sortByCreation().map(toMessageRow)
    rows.forEach((row, index) => {
      // The rail's line runs down to the next marker, so only the final row stops short.
      // Chat has no rail to draw: the messages no longer share a column to hang off.
      const last = index === rows.length - 1
      row.railHeight = isChat.value ? '0px' : last ? '20px' : '100%'
      // The timeline names the sender inside the card, where it reads as a record's
      // heading. Chat says it above the bubble instead, so the bubble holds the message
      // and nothing else — and someone writing twice in a row says it once, because the
      // second message is the same turn continuing.
      const opens = !continues(rows[index - 1], row)
      row.insideByline = !isChat.value
      row.outsideByline = isChat.value && opens
      // One face per turn. The rail keeps its width either way, so a grouped message stays
      // lined up with the one it follows instead of sliding into the empty gutter.
      row.showAvatar = !isChat.value || opens
    })
    // The gap belongs to the message above the join, since that is where it is drawn.
    rows.forEach((row, index) => {
      const next = rows[index + 1]
      row.rowSpacing = next && isChat.value && !next.outsideByline ? GROUPED_GAP : ROW_GAP
    })
    return rows
  })

  /** Whether this message carries on from the one before: same person, same side of the
   *  conversation, close enough in time to still be the same breath. */
  function continues(previous, row) {
    if (!previous) return false
    return (
      previous.isAgentReply === row.isAgentReply &&
      previous.sender === row.sender &&
      dayjs(row.creation).diff(dayjs(previous.creation), 's') <= GROUP_SECONDS
    )
  }

  // The agent portal lands the reader on the newest message a second after the
  // thread arrives, or on the one the URL hash names — `TicketConversation` waits
  // the same second, because the email frames only size themselves after paint.
  let landed = false
  watch(conversation, (messages) => {
    if (landed || !messages.length) return
    landed = true
    const id = location.hash.slice(1) || messages[messages.length - 1].name
    setTimeout(() => document.getElementById(id)?.scrollIntoView({ block: 'nearest' }), 1000)
  })

  function sortByCreation() {
    return [...(ticket.data?.communications || [])].sort(
      (first, second) =>
        new Date(first.creation).getTime() - new Date(second.creation).getTime(),
    )
  }

  function toMessageRow(message) {
    return {
      name: message.name,
      content: message.content,
      sender: message.user?.name || message.sender,
      image: message.user?.image,
      // Kept raw as well as worded: the sidebar's timeline dates and measures it.
      creation: message.creation,
      timeAgo: timeAgo(message.creation),
      clock: clockTime(message.creation),
      fullDate: dayjs(message.creation).format(DATE_FORMAT),
      attachments: message.attachments || [],
      // Whether support wrote it. Frappe already records the direction, so ask it rather
      // than comparing identities: `sender` is an email while `raised_by` can be a User
      // docname ("Administrator"), and that mismatch made every message — the customer's
      // own included — look like an agent reply.
      isAgentReply: message.sent_or_received === 'Sent',
      railHeight: '100%',
      ...layoutOf(isChat.value, message.sent_or_received !== 'Sent'),
    }
  }

  /** The newest message from support — what the "did this solve it?" prompt hangs off. */
  const lastAgentReply = computed(
    () => [...conversation.value].reverse().find((row) => row.isAgentReply) || null,
  )

  // When support first answered. Deliberately a message and not the ticket's
  // `first_responded_on`: that field is stamped on a status transition — into Paused,
  // or Open to Resolved — so it misses a ticket that was answered and left open, and
  // invents one for a ticket resolved without a word.
  const firstAgentReply = computed(
    () => conversation.value.find((row) => row.isAgentReply) || null,
  )

  // The customer's own rating, told back to them at the foot of the summary rather than
  // in the thread: it is a fact about the ticket, not a message in the conversation.
  // Dated from `resolution_date` because HD Ticket stamps no time of its own for feedback —
  // it is collected as part of closing, so that is the closest true moment.
  const rating = computed(() => toRating())

  function toRating() {
    const data = ticket.data
    if (!data?.feedback_rating) return null
    const when = data.resolution_date || data.modified
    return {
      name: 'feedback',
      // HD Ticket stores the rating as a fraction; the Rating component counts stars.
      rating: data.feedback_rating * 5,
      tags: feedbackTags(data.feedback),
      comment: data.feedback_extra || '',
      timeAgo: timeAgo(when),
      fullDate: dayjs(when).format(DATE_FORMAT),
    }
  }

  /** The preset answer reads as tags — "Adequate help, bit slow" is two of them — so it is
   *  split the way the agent portal's own Feedback section splits it. */
  function feedbackTags(feedback: string) {
    return (feedback || '')
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => ({ label: part.charAt(0).toUpperCase() + part.slice(1) }))
  }

  /** "2:14 PM" today, and the day it happened before that — the reference's own wording. */
  function clockTime(value: string) {
    const at = dayjs(value)
    const time = at.format(CLOCK_FORMAT)
    if (at.isSame(dayjs(), 'day')) return time
    const day = at.isSame(dayjs(), 'year') ? DAY_FORMAT : YEAR_FORMAT
    return `${at.format(day)} at ${time}`
  }

  return {
    rating,
    lastAgentReply,
    firstAgentReply,
    conversation,
    ...useOutsideHoursBanner(ticket),
    ...useReplyComposer(ticket),
  }
}

// The same endpoint the agent portal asks, and the same dismissal: remembered per
// ticket per day, so it returns tomorrow if the ticket is still unanswered.
function useOutsideHoursBanner(ticket) {
  const banner = createResource({
    url: 'helpdesk.helpdesk.doctype.hd_ticket.api.show_outside_hours_banner',
    makeParams: () => ({ ticket_name: ticket.data?.name }),
  })
  const dismissed = ref(false)

  watch(
    () => ticket.data?.name,
    (name) => {
      if (!name) return
      dismissed.value = localStorage.getItem(dismissKey(name)) === 'true'
      banner.fetch()
    },
    { immediate: true },
  )

  function dismissKey(name: string) {
    return `dismissBanner_${name}_${new Date().toISOString().split('T')[0]}`
  }

  function dismissBanner() {
    localStorage.setItem(dismissKey(ticket.data.name), 'true')
    dismissed.value = true
  }

  return {
    showBanner: computed(() => Boolean(banner.data?.show) && !dismissed.value),
    bannerMessage: computed(() => banner.data?.msg || ''),
    dismissBanner,
  }
}
