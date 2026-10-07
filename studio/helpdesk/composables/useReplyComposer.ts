import { computed, ref } from 'vue'
import { call, useFileUpload } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { isClosedStatus } from '@app/stores/ticketMeta'
import { CUSTOMER_FILE_TYPES, runAction } from '@app/utils'

export function useReplyComposer(ticket, config) {
  const isComposerOpen = ref(false)
  const reply = ref('')
  const isSending = ref(false)
  // The composer sits over the thread; it reports its height and the thread keeps that much clear.
  const composerReserve = ref(0)

  const canReply = computed(() => !isClosedStatus(ticket.data?.status))

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

  const acceptedFileTypes = computed(() => (config.value?.is_agent ? undefined : CUSTOMER_FILE_TYPES.join(',')))

  function discard() {
    reply.value = ''
    isComposerOpen.value = false
  }

  function send({ body, attachments }) {
    if (isContentEmpty(body)) return
    return runAction(
      async () => {
        await call('run_doc_method', {
          dt: 'HD Ticket',
          dn: ticket.data.name,
          method: 'create_communication_via_contact',
          args: { message: body, attachments },
        })
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
