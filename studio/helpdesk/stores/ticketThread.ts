import { computed, nextTick, ref, watch } from 'vue'
import { call, createResource, dayjs, toast } from 'frappe-ui'
import { usePreferences } from '@app/stores/preferences'

// The message thread, the outside-working-hours banner and the reply composer —
// the data behind `desk/src/pages/ticket/TicketConversation.vue` and
// `TicketTextEditor.vue`. The page draws all of it from Studio blocks, so every
// value a block binds is finished here: no formatting is left to an expression.

const DATE_FORMAT = 'ddd, MMM D, YYYY h:mm A'
// Chat stamps the clock, the way every chat does: a message is a moment, not an age.
const CLOCK_FORMAT = 'h:mm A'
const DAY_FORMAT = 'D MMMM'
const YEAR_FORMAT = 'D MMMM YYYY'
const UPLOAD_ARGS = { folder: 'Home/Helpdesk', private: true }

// The two thread layouts, as the style values the blocks bind — Studio evaluates
// `baseStyles`, so a row carries its own geometry rather than the page forking into two
// templates. Timeline is the default: every message in one column, hung off the rail.
const TIMELINE = {
  // The face lives beside the card, never in it — the rail is its column.
  showRail: true,
  // Lined up with the first line of the card, which is the byline.
  avatarOffset: '6px',
  avatarLeft: '0px',
  rowDisplay: 'grid',
  rowDirection: 'row',
  // How far the row sits from the thread's own left edge. The timeline starts at it.
  rowLeft: '0px',
  contentAlign: 'stretch',
  // A record, not a bubble: the card takes the column and every message lines up.
  cardWidth: 'auto',
  cardMaxWidth: 'none',
  cardPadding: '10px 12px 8px',
  cardBackground: 'var(--surface-elevation-1)',
  cardBorder: '1px solid var(--outline-gray-2)',
}
// Chat drops the grid for a flex row, so the reader's own messages can turn around and
// sit against the other edge. A bubble is as wide as what was said and no wider: the frame
// inside reports the width its content wants (`hug` in KbEmailContent), so the card can
// shrink to it, and three quarters of the column is where a long message stops and wraps
// instead of running the width of the thread.
const THEIR_BUBBLE = {
  ...TIMELINE,
  // Chat's byline sits above the bubble, so the face sits at the top of the row and shifts
  // in towards the name it belongs to.
  avatarOffset: '-4px',
  avatarLeft: '23px',
  rowDisplay: 'flex',
  contentAlign: 'flex-start',
  // Chat pulls an incoming row out past that edge, so the face — not the bubble — is what
  // lines up with everything else in the column.
  rowLeft: '-16px',
  cardWidth: 'fit-content',
  cardMaxWidth: '76%',
  cardPadding: '12px 16px 14px',
}
// How long a run of messages stays one turn, and how tightly those messages sit.
const GROUP_SECONDS = 5 * 60
const GROUPED_GAP = '12px'
const ROW_GAP = '24px'

const OWN_BUBBLE = {
  ...THEIR_BUBBLE,
  // Nobody needs their own face shown back at them: the side of the thread says whose it
  // is, so the bubble takes the whole width and sits flush against the edge.
  showRail: false,
  rowDirection: 'row-reverse',
  // Nothing hangs off the left of your own message, so it keeps to the edge.
  rowLeft: '0px',
  contentAlign: 'flex-end',
  // Tinted and borderless, the way every chat marks the side you are on.
  cardBackground: 'var(--surface-gray-1)',
  cardBorder: '1px solid transparent',
}

export function useTicketThread(ticket) {
  const { conversationLayout } = usePreferences()
  const isChat = computed(() => conversationLayout.value === 'chat')

  /** The layout values a row carries, by whose message it is. */
  function layoutOf(isOwn: boolean) {
    if (!isChat.value) return TIMELINE
    return isOwn ? OWN_BUBBLE : THEIR_BUBBLE
  }

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
      ...layoutOf(message.sent_or_received !== 'Sent'),
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

  // `prettyDate` from desk/src/utils.ts, not dayjs's own `fromNow`: the agent portal
  // words a week as a week where dayjs would still be counting days.
  function timeAgo(value: string) {
    const seconds = dayjs().diff(dayjs(value), 'second')
    const days = Math.floor(seconds / 86400)
    if (days < 1) return withinDay(seconds)
    if (days < 2) return 'Yesterday'
    return olderThanDay(days)
  }

  function withinDay(seconds: number) {
    if (seconds < 60) return 'Just now'
    if (seconds < 120) return '1 minute ago'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 7200) return '1 hour ago'
    return `${Math.floor(seconds / 3600)} hours ago`
  }

  function olderThanDay(days: number) {
    if (days < 7) return `${days} days ago`
    if (days < 14) return '1 week ago'
    if (days < 31) return `${Math.floor(days / 7)} weeks ago`
    if (days < 62) return '1 month ago'
    if (days < 365) return `${Math.floor(days / 30)} months ago`
    if (days < 730) return '1 year ago'
    return `${Math.floor(days / 365)} years ago`
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

// How much of the thread the composer covers, by state. It floats over the messages, so
// the thread reserves the room rather than being overlapped: enough for the one-line
// prompt, and enough for the open editor (measured at 194px, plus room to breathe).
const PROMPT_TAIL = '96px'
const EDITOR_TAIL = '208px'
/** Long enough for the message frames to have reported their real height. */
const SETTLE_MS = 300
/** The ride down, matched to the editor's own opening so they read as one movement. */
const SCROLL_MS = 220

function useReplyComposer(ticket) {
  const composerOpen = ref(false)
  const reply = ref('')
  const attachments = ref<any[]>([])
  const sending = ref(false)

  // Only a closed ticket refuses replies — `TicketCustomer.vue`'s `showEditor`.
  // Resolved is not closed: replying to it reopens the ticket, which is what
  // `create_communication_via_contact` does with `ticket_reopen_status`.
  const canReply = computed(() => ticket.data?.status !== 'Closed')

  // Tags alone are not a message: an empty editor still reports `<p></p>`.
  const canSend = computed(
    () => reply.value.replace(/<[^>]*>/g, '').trim().length > 0,
  )

  /** The space the thread keeps clear beneath itself for whatever the composer is. */
  const threadTailSpace = computed(() =>
    composerOpen.value ? EDITOR_TAIL : PROMPT_TAIL,
  )

  function openComposer() {
    composerOpen.value = true
    // The editor is some 110px taller than the prompt it replaces, and it opens over the
    // thread — so the message being replied to would end up behind it. Riding the thread
    // down to its new end carries that message up above the composer instead, and reads
    // as one movement with the editor growing into place.
    nextTick(scrollThreadToEnd)
    // Message bodies are iframes and settle their height a beat after they paint, which
    // moves the end of the thread out from under the first pass. This one catches it.
    setTimeout(scrollThreadToEnd, SETTLE_MS)
  }

  /** Ride the thread down to its new end.
   *
   *  Animated by hand rather than with `behavior: 'smooth'`, which this container ignores
   *  — `scrollTo` and `scrollBy` both leave it where it was, while assigning `scrollTop`
   *  moves it. Same ease-out as the editor's own opening, so the two read as one movement.
   */
  function scrollThreadToEnd() {
    const thread = document.querySelector(
      '[data-component-id="container-ticket-thread"]',
    )
    if (!thread) return
    const from = thread.scrollTop
    const distance = thread.scrollHeight - thread.clientHeight - from
    if (distance <= 0) return

    const started = performance.now()
    const step = (now: number) => {
      const progress = Math.min((now - started) / SCROLL_MS, 1)
      thread.scrollTop = from + distance * (1 - (1 - progress) ** 3)
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }

  function setReply(content: string) {
    reply.value = content
  }

  function addAttachment(file) {
    attachments.value = [...attachments.value, file]
  }

  function removeAttachment(file) {
    attachments.value = attachments.value.filter(
      (attached) => attached.file_url !== file.file_url,
    )
  }

  function discard() {
    reply.value = ''
    attachments.value = []
    composerOpen.value = false
  }

  // `create_communication_via_contact` is the requester's reply path — it is what
  // attributes the message to them rather than to an agent.
  async function send() {
    if (!canSend.value || sending.value) return
    sending.value = true
    try {
      await call('run_doc_method', {
        dt: 'HD Ticket',
        dn: ticket.data.name,
        method: 'create_communication_via_contact',
        args: { message: reply.value, attachments: attachments.value },
      })
      discard()
      await ticket.fetch()
      // What was just written is the point of the thread now, and the composer has folded
      // back to a line — so ride down to it rather than leaving it behind the editor.
      nextTick(scrollThreadToEnd)
      setTimeout(scrollThreadToEnd, SETTLE_MS)
    } catch (error) {
      toast.error(error?.messages?.[0] || 'Could not send the message')
    } finally {
      sending.value = false
    }
  }

  return {
    canReply,
    composerOpen,
    threadTailSpace,
    openComposer,
    reply,
    setReply,
    attachments,
    addAttachment,
    removeAttachment,
    uploadArgs: UPLOAD_ARGS,
    canSend,
    sending,
    send,
    discard,
  }
}
