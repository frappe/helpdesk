import { computed, ref } from 'vue'
import { call, useFileUpload } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { isContentEmpty } from '@helpdesk/shared/utils'
import { isClosedStatus } from '@app/stores/ticketMeta'
import { runAction } from '@app/utils'

// The composer floats over the thread, so the thread reserves this much room for it.
const PROMPT_TAIL = '96px'
const EDITOR_TAIL = '208px'

export function useReplyComposer(ticket) {
  const isComposerOpen = ref(false)
  const reply = ref('')
  const isSending = ref(false)

  const canReply = computed(() => !isClosedStatus(ticket.data?.status))
  const threadTailSpace = computed(() => (isComposerOpen.value ? EDITOR_TAIL : PROMPT_TAIL))

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
    threadTailSpace,
    openComposer,
    reply,
    isSending,
    uploadFile,
    send,
  }
}
