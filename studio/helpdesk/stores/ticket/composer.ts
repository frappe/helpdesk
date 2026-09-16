import { computed, nextTick, ref } from 'vue'
import { call, toast } from 'frappe-ui'

const UPLOAD_ARGS = { folder: 'Home/Helpdesk', private: true }

// The composer floats over the thread, so the thread reserves this much room for it.
const PROMPT_TAIL = '96px'
const EDITOR_TAIL = '208px'
// Long enough for the message frames to have reported their real height.
const SETTLE_MS = 300
// Matched to the editor's own opening, so the two read as one movement.
const SCROLL_MS = 220

export function useReplyComposer(ticket) {
  const composerOpen = ref(false)
  const reply = ref('')
  const attachments = ref<any[]>([])
  const sending = ref(false)

  // Resolved is not closed: replying to it reopens the ticket.
  const canReply = computed(() => ticket.data?.status !== 'Closed')

  // An empty editor still reports `<p></p>`.
  const canSend = computed(
    () => reply.value.replace(/<[^>]*>/g, '').trim().length > 0,
  )

  const threadTailSpace = computed(() =>
    composerOpen.value ? EDITOR_TAIL : PROMPT_TAIL,
  )

  function openComposer() {
    composerOpen.value = true
    // The editor opens over the thread, so ride down or the message replied to is behind it.
    nextTick(scrollThreadToEnd)
    // Message iframes settle their height a beat after paint; this pass catches that.
    setTimeout(scrollThreadToEnd, SETTLE_MS)
  }

  // Animated by hand: this container ignores `behavior: 'smooth'` but honours `scrollTop`.
  function scrollThreadToEnd() {
    // A class of ours, not the studio block id, which renaming the block would change.
    const thread = document.querySelector('.js-ticket-thread')
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

  // The requester's reply path: it attributes the message to them, not to an agent.
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
