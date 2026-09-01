import { computed, nextTick, ref } from 'vue'
import { call, toast } from 'frappe-ui'

// The reply composer: what can be said, what rides along with it, and the choreography
// of the thread making room — the data behind `desk/src/pages/ticket/TicketTextEditor.vue`.

const UPLOAD_ARGS = { folder: 'Home/Helpdesk', private: true }

// How much of the thread the composer covers, by state. It floats over the messages, so
// the thread reserves the room rather than being overlapped: enough for the one-line
// prompt, and enough for the open editor (measured at 194px, plus room to breathe).
const PROMPT_TAIL = '96px'
const EDITOR_TAIL = '208px'
/** Long enough for the message frames to have reported their real height. */
const SETTLE_MS = 300
/** The ride down, matched to the editor's own opening so they read as one movement. */
const SCROLL_MS = 220

export function useReplyComposer(ticket) {
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
