import { computed, ref, watch, type Ref } from 'vue'
import { createResource } from 'frappe-ui'
import { useArticleSearch } from '@app/composables/useArticleSearch'
import { useSession } from '@app/stores/session'

const MATCH_LIMIT = 6

export function useAiAnswer(question: Ref<string>) {
  const session = useSession()
  const answer = createResource({
    url: 'helpdesk.api.knowledge_base.answer_question',
    method: 'POST',
    makeParams: () => ({ question: question.value }),
  })

  // Plain matches stand in while AI search is off, or when the answer fails.
  const matchQuery = ref('')
  const matches = useArticleSearch(matchQuery, { limit: MATCH_LIMIT })

  const isReady = computed(() => Boolean(session.config.value))
  const isAiOn = computed(() => session.isAiSearchEnabled.value)
  const isFailed = computed(() => Boolean(answer.error))
  const showMatches = computed(() => isReady.value && (!isAiOn.value || isFailed.value))
  const isLoading = computed(() => !isReady.value || (isAiOn.value && !answer.data && !isFailed.value))

  watch(
    [isReady, isAiOn, question],
    ([ready, on, text]) => {
      answer.abort()
      answer.reset()
      matchQuery.value = ''
      if (!ready) return
      // A failed answer falls back to plain matches, so the rejection is not news.
      if (on && text) answer.submit().catch(() => {})
      else matchQuery.value = text
    },
    { immediate: true },
  )
  watch(isFailed, (failed) => failed && (matchQuery.value = question.value))

  return { answer, matches, isAiOn, isFailed, isLoading, showMatches }
}
