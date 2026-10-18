import { computed, ref } from 'vue'
import { call, useFileUpload } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty, runAction, uploadableFileTypes } from '@helpdesk/shared/utils'

export function useReplyComposer(ticket, { isClosed, isAgent }) {
  const isComposerOpen = ref(false)
  const reply = ref('')
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
    if (isContentEmpty(body)) return
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
