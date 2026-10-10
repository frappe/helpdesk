import { call } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { runAction } from '@app/utils'

// Values match HD Article Feedback: 1 like, 2 dislike; 0 clears.
// A function, not a constant, so the labels are translated after translations load.
export function feedbackAnswers() {
  return [
    { value: 1, label: __('Yes, it was helpful') },
    { value: 2, label: __("No, it wasn't helpful") },
  ] as const
}

// A second click on the current answer clears it.
export function saveArticleFeedback(
  article: string,
  current: number | undefined,
  answer: number,
  onSaved: (value: number) => void,
) {
  const value = current === answer ? 0 : answer
  return runAction(
    async () => {
      await call('helpdesk.api.knowledge_base.set_article_feedback', { article, value })
      onSaved(value)
    },
    { success: __('Thanks for your feedback!'), fallback: __('Could not submit feedback') },
  )
}
