import { computed, reactive, ref, watch } from 'vue'
import { frappeRequest } from 'frappe-ui'

// Matches `limit` on the category page's `articles` resource.
const PAGE_LENGTH = 20

type Article = { name: string; title: string; title_slug?: string; excerpt?: string }

// `firstPage` is the page's own resource; this appends what comes after it.
export function useMoreArticles(firstPage: { data: Article[] | null }, category: () => unknown) {
  let latest: Promise<Article[]> | undefined
  const nextPages = ref<Article[]>([])

  const more = reactive({
    // An article published mid-scroll pushes the previous page's last row into the next.
    rows: computed(() => {
      const rows = [...(firstPage.data || []), ...nextPages.value]
      return [...new Map(rows.map((row) => [row.name, row])).values()]
    }),
    hasMore: false,
    loading: false,
    failed: false,
    loadMore,
  })

  async function loadMore() {
    if (more.loading || !more.hasMore) return
    more.loading = true
    more.failed = false
    const start = (firstPage.data?.length ?? 0) + nextPages.value.length
    const request = frappeRequest({
      url: 'helpdesk.api.knowledge_base.get_articles',
      method: 'GET',
      params: { category: category(), start, limit: PAGE_LENGTH },
    })
    latest = request
    try {
      const rows = await request
      if (request !== latest) return
      nextPages.value.push(...rows)
      more.hasMore = rows.length === PAGE_LENGTH
    } catch {
      if (request === latest) more.failed = true
    } finally {
      if (request === latest) more.loading = false
    }
  }

  // A new first page drops the old pages, and any request still running for them.
  watch(
    () => firstPage.data,
    (rows) => {
      latest = undefined
      nextPages.value = []
      more.loading = false
      more.failed = false
      more.hasMore = rows?.length === PAGE_LENGTH
    },
    { immediate: true },
  )

  return more
}
