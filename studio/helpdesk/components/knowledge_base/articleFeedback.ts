import { ref } from 'vue'
import { call } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { runAction } from '@helpdesk/shared/utils'

// One vote in flight: the server's check-then-insert would record a double-click twice.
const saving = ref(false)

export function saveArticleFeedback(
  article: string,
  current: number | undefined,
  answer: number,
  onSaved: (value: number) => void,
) {
  const value = current === answer ? 0 : answer
  return runAction(
    async () => {
      await call('helpdesk.api.knowledge_base.vote_on_article', { article, vote: value })
      onSaved(value)
    },
    { busy: saving, success: __('Thanks for your feedback!'), fallback: __('Could not submit feedback') },
  )
}
