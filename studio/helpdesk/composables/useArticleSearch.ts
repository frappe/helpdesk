import { computed, reactive, toRefs, watch, type Ref } from 'vue'
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

const PAGE_LENGTH = 20

type SearchHit = { name: string; title: string; title_slug?: string; excerpt?: string; minutes?: number; category_label?: string }

// The search page: pages of 20, with match counts per Category for the filter.
export function usePagedArticleSearch(query: Ref<string>, categories: Ref<string[]>) {
  const state = reactive({
    rows: [] as SearchHit[],
    total: 0,
    counts: {} as Record<string, number>,
    // The query and filter the rows answer, as `key()` gives them.
    settledKey: null as string | null,
  })
  const key = (text = query.value, category = JSON.stringify(categories.value)) => `${text.trim()}\n${category}`
  const settle = () => (state.settledKey = key(page.params.query, page.params.category))
  const page = createResource({
    url: 'helpdesk.api.knowledge_base.search_articles',
    method: 'GET',
    makeParams: ({ start }) => ({
      query: query.value,
      category: JSON.stringify(categories.value),
      start,
      page_length: PAGE_LENGTH,
    }),
    onSuccess(data) {
      state.rows = page.params.start ? [...state.rows, ...data.results] : data.results
      state.total = data.total
      state.counts = data.categories
      settle()
    },
    onError() {
      // Old rows must not stand in as answers to the new query
      if (!page.params.start) Object.assign(state, { rows: [], total: 0, counts: {} })
      settle()
    },
  })

  const search = debounce(() => {
    // fetch() keeps stale in-flight responses; abort so they can't overwrite
    page.abort()
    state.settledKey = null
    if ((query.value || '').trim().length >= MIN_QUERY_LENGTH) return page.fetch({ start: 0 })
    page.reset()
    Object.assign(state, { rows: [], total: 0, counts: {} })
  }, SEARCH_DEBOUNCE_MS)
  watch(() => key(), search, { immediate: true })

  const isCurrent = computed(() => state.settledKey === key())
  const hasMore = computed(() => state.rows.length < state.total)

  function loadMore() {
    if (isCurrent.value && hasMore.value && !page.loading) page.fetch({ start: state.rows.length })
  }

  const { rows, total, counts } = toRefs(state)
  return reactive({
    rows,
    total,
    counts,
    hasMore,
    isCurrent,
    isLoading: computed(() => page.loading),
    loadMore,
  })
}
