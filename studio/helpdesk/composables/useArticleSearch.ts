import { watch, type Ref } from 'vue'
import { createResource, debounce } from 'frappe-ui'
import { SEARCH_DEBOUNCE_MS } from '@app/utils'

export const MIN_QUERY_LENGTH = 3

export function useArticleSearch(query: Ref<string>, { limit = 0 } = {}) {
  const results = createResource({
    url: 'helpdesk.api.knowledge_base.search_articles',
    method: 'GET',
    makeParams: () => ({ query: query.value, ...(limit && { limit }) }),
  })

  const search = debounce(() => {
    // fetch() doesn't drop an older in-flight response, so a slow one would overwrite this query's
    results.abort()
    if ((query.value || '').trim().length >= MIN_QUERY_LENGTH) results.fetch()
    else results.reset()
  }, SEARCH_DEBOUNCE_MS)
  watch(query, search, { immediate: true })

  return results
}
