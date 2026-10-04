import { watch, type Ref } from 'vue'
import { createResource, debounce } from 'frappe-ui'
import { SEARCH_DEBOUNCE_MS } from '@app/utils'

const MIN_QUERY_LENGTH = 3

export function useArticleSearch(query: Ref<string>, { limit = 0, minLength = MIN_QUERY_LENGTH } = {}) {
  const results = createResource({
    url: 'helpdesk.api.knowledge_base.search_articles',
    method: 'GET',
    makeParams: () => ({ query: query.value, ...(limit && { limit }) }),
  })

  const search = debounce(() => {
    if ((query.value || '').trim().length >= minLength) results.fetch()
    else results.reset()
  }, SEARCH_DEBOUNCE_MS)
  watch(query, search, { immediate: true })

  return results
}
