import { computed, ref, watch } from 'vue'
import { call, useFileUpload } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty, runAction, uploadableFileTypes } from '@helpdesk/shared/utils'

export function useReplyComposer(ticket, { ticketId, isClosed, isAgent }) {
  const isComposerOpen = ref(false)
  const reply = ref('')

  // A draft stays with its ticket: switching swaps it in before the next render.
  const drafts = new Map<string, { reply: string; open: boolean }>()
  watch(
    ticketId,
    (next, previous) => {
      if (previous) drafts.set(previous, { reply: reply.value, open: isComposerOpen.value })
      const draft = drafts.get(next)
      reply.value = draft?.reply || ''
      isComposerOpen.value = draft?.open || false
    },
    { flush: 'sync' },
  )
  const isSending = ref(false)
  // Composer overlays the thread; its height is kept clear below.
  const composerReserve = ref(0)

  const canReply = computed(() => !isClosed.value)

  function uploadFile(file: File) {
    return useFileUpload().upload(file, {
      private: true,
      doctype: 'HD Ticket',
      docname: ticket.data?.name,
    })
  }

  const acceptedFileTypes = computed(() => uploadableFileTypes(isAgent.value)?.join(','))

  function discard() {
    reply.value = ''
    isComposerOpen.value = false
  }

  async function send({ body, attachments, reset }) {
    // An attachment alone is a reply; the composer enables Send for it.
    if (isContentEmpty(body) && !attachments?.length) return
    const sent = await runAction(
      async () => {
        await call('run_doc_method', {
          dt: 'HD Ticket',
          dn: ticket.data.name,
          method: 'create_communication_via_contact',
          args: { message: body, attachments },
        })
        reset()
        discard()
      },
      { busy: isSending, fallback: __('Could not send the message') },
    )
    // Outside the action: a failed refetch must not trigger a resend.
    if (sent) ticket.fetch()
    return sent
  }

  return {
    canReply,
    isComposerOpen,
    composerReserve,
    reply,
    isSending,
    uploadFile,
    acceptedFileTypes,
    send,
  }
}
