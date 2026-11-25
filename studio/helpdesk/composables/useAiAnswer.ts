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

  // Plain matches stand in while AI search is off or the answer fails.
  const matchQuery = ref('')
  const matches = useArticleSearch(matchQuery, { limit: MATCH_LIMIT })

  const isReady = computed(() => Boolean(session.config.value))
  const isAiOn = computed(() => session.isAiSearchEnabled.value)
  const isEmpty = computed(() => !(question.value || '').trim())
  const isFailed = computed(() => Boolean(answer.error))
  const showMatches = computed(() => isReady.value && !isEmpty.value && (!isAiOn.value || isFailed.value))
  const isLoading = computed(
    () => !isReady.value || (!isEmpty.value && isAiOn.value && !answer.data && !isFailed.value),
  )

  watch(
    [isReady, isAiOn, question],
    ([ready, on, text]) => {
      answer.abort()
      answer.reset()
      matchQuery.value = ''
      if (!ready) return
      if (!(text || '').trim()) return
      // A failed answer falls back to plain matches, so the rejection is not news.
      if (on) answer.submit().catch(() => {})
      else matchQuery.value = text
    },
    { immediate: true },
  )
  watch(isFailed, (failed) => failed && (matchQuery.value = question.value))

  return { answer, matches, isEmpty, isFailed, isLoading, showMatches }
}
