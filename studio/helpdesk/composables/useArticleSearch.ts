import { watch, type Ref } from 'vue'
import { createResource, debounce } from 'frappe-ui'
import { SEARCH_DEBOUNCE_MS } from '@helpdesk/shared/utils'

export const MIN_QUERY_LENGTH = 3

export function useArticleSearch(query: Ref<string>, { limit = 0 } = {}) {
  // The query `data` answers. Not `loading`: an aborted fetch clears it
  // while the newer one is still in flight.
  const settle = () => (results.settledQuery = results.params.query.trim())
  const results = createResource({
    url: 'helpdesk.api.knowledge_base.search_articles',
    method: 'GET',
    makeParams: () => ({ query: query.value, ...(limit && { limit }) }),
    onSuccess: settle,
    onError: settle,
  })

  const search = debounce(() => {
    // fetch() keeps stale in-flight responses; abort so they can't overwrite
    results.abort()
    results.settledQuery = null
    if ((query.value || '').trim().length >= MIN_QUERY_LENGTH) results.fetch()
    else results.reset()
  }, SEARCH_DEBOUNCE_MS)
  watch(query, search, { immediate: true })

  return results
}
