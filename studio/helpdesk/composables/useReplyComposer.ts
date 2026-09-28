import { computed, nextTick, ref } from 'vue'
import { call } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { isClosedStatus } from '@app/stores/ticketMeta'
import { runAction } from '@app/utils'

// The composer floats over the thread, so the thread reserves this much room for it.
const PROMPT_TAIL = '96px'
const EDITOR_TAIL = '208px'
// Long enough for the message frames to have reported their real height.
const SETTLE_MS = 300
// Matched to the editor's own opening, so the two read as one movement.
const SCROLL_MS = 220

export function useReplyComposer(ticket) {
  const isComposerOpen = ref(false)
  const reply = ref('')
  const attachments = ref<any[]>([])
  const isSending = ref(false)

  // Resolved is not closed: replying to it reopens the ticket.
  const canReply = computed(() => !isClosedStatus(ticket.data?.status))
  const canSend = computed(() => !isContentEmpty(reply.value))
  const threadTailSpace = computed(() => (isComposerOpen.value ? EDITOR_TAIL : PROMPT_TAIL))

  function openComposer() {
    isComposerOpen.value = true
    scrollThreadToEndSoon()
  }

  // Once now, once after the message frames have settled their height.
  function scrollThreadToEndSoon() {
    nextTick(scrollThreadToEnd)
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

  function addAttachment(file) {
    attachments.value = [...attachments.value, file]
  }

  function removeAttachment(file) {
    attachments.value = attachments.value.filter((attached) => attached.file_url !== file.file_url)
  }

  function discard() {
    reply.value = ''
    attachments.value = []
    isComposerOpen.value = false
  }

  // The requester's reply path: it attributes the message to them, not to an agent.
  function send() {
    if (!canSend.value) return
    return runAction(
      async () => {
        await call('run_doc_method', {
          dt: 'HD Ticket',
          dn: ticket.data.name,
          method: 'create_communication_via_contact',
          args: { message: reply.value, attachments: attachments.value },
        })
        discard()
        await ticket.fetch()
        scrollThreadToEndSoon()
      },
      { busy: isSending, fallback: __('Could not send the message') },
    )
  }

  return {
    canReply,
    isComposerOpen,
    threadTailSpace,
    openComposer,
    reply,
    attachments,
    addAttachment,
    removeAttachment,
    isSending,
    send,
    discard,
  }
}
