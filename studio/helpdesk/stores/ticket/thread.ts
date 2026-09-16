import { computed, ref, watch } from 'vue'
import { timeAgo } from '@app/utils'
import { createResource, dayjs } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'
import { layoutOf, GROUP_SECONDS, GROUPED_GAP, ROW_GAP } from '@app/components/ticket/bubbleLayout'
import { useReplyComposer } from './composer'

// Drawn from Studio blocks, so every value a block binds is finished here.

const DATE_FORMAT = 'ddd, MMM D, YYYY h:mm A'
const CLOCK_FORMAT = 'h:mm A'
const DAY_FORMAT = 'D MMMM'
const YEAR_FORMAT = 'D MMMM YYYY'
export function useTicketThread(ticket) {
  const { conversationLayout } = usePreferences()
  const isChat = computed(() => conversationLayout.value === 'chat')

  const conversation = computed(() => {
    const rows = sortByCreation().map(toMessageRow)
    rows.forEach((row, index) => {
      // Only the final row stops short, and chat has no rail at all.
      const last = index === rows.length - 1
      row.railHeight = isChat.value ? '0px' : last ? '20px' : '100%'
      // Chat puts the byline above the bubble, once per turn rather than once per message.
      const opens = !continues(rows[index - 1], row)
      row.insideByline = !isChat.value
      row.outsideByline = isChat.value && opens
      // One face per turn; the rail keeps its width either way, so rows stay lined up.
      row.showAvatar = !isChat.value || opens
    })
    // The gap belongs to the message above the join, since that is where it is drawn.
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

  // The wait is because the email frames only size themselves after paint.
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
      // Kept raw as well as worded: the sidebar dates and measures it.
      creation: message.creation,
      timeAgo: timeAgo(message.creation),
      clock: clockTime(message.creation),
      fullDate: dayjs(message.creation).format(DATE_FORMAT),
      attachments: message.attachments || [],
      // Ask Frappe's direction, not identities: `sender` is an email, `raised_by` may not be.
      isAgentReply: message.sent_or_received === 'Sent',
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

  // The preset answer reads as tags: "Adequate help, bit slow" is two of them.
  function feedbackTags(feedback: string) {
    return (feedback || '')
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => ({ label: part.charAt(0).toUpperCase() + part.slice(1) }))
  }

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

// Dismissal is remembered per ticket per day, so it returns tomorrow.
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
    return `kb:banner-dismissed:${name}:${new Date().toISOString().split('T')[0]}`
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
