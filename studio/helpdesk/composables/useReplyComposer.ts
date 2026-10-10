import { computed, ref } from 'vue'
import { call, useFileUpload } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { runAction, uploadableFileTypes } from '@app/utils'

export function useReplyComposer(ticket, { isClosed, isAgent }) {
  // Open on arrival, so the customer can start typing their reply straight away.
  const isComposerOpen = ref(true)
  const reply = ref('')
  const isSending = ref(false)
  // The composer sits over the thread; it reports its height and the thread keeps that much clear.
  const composerReserve = ref(0)

  const canReply = computed(() => !isClosed.value)

  function openComposer() {
    isComposerOpen.value = true
  }

  // Inline images and attachments alike; the send links each by its File `name`.
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

  function send({ body, attachments, reset }) {
    if (isContentEmpty(body)) return
    return runAction(
      async () => {
        await call('run_doc_method', {
          dt: 'HD Ticket',
          dn: ticket.data.name,
          method: 'create_communication_via_contact',
          args: { message: body, attachments },
        })
        reset()
        discard()
        await ticket.fetch()
      },
      { busy: isSending, fallback: __('Could not send the message') },
    )
  }

  return {
    canReply,
    isComposerOpen,
    composerReserve,
    openComposer,
    reply,
    isSending,
    uploadFile,
    acceptedFileTypes,
    send,
  }
}
