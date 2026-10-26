import { reactive, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { createResource, frappeRequest } from 'frappe-ui'

// Module-level, not `cache`: what a reader sees depends on who they are.
const sidebar = createResource({
  url: 'helpdesk.api.knowledge_base.get_kb_sidebar',
  method: 'GET',
})

export function useKnowledgeBase() {
  if (!sidebar.data && !sidebar.loading) sidebar.fetch()
  return { sidebar }
}

// Survives the sidebar's remount on each page.
export const sidebarState = {
  query: ref(''),
  openName: ref<string | null>(null),
  shown: reactive<Record<string, number>>({}),
  scrollTop: 0,
}

const ARTICLE_CACHE_SIZE = 30
// Reuse a fetched article for 60s (hover then click, a quick back), then fetch it again so edits show up
const ARTICLE_MAX_AGE_MS = 60_000
const HOVER_DELAY = 80
const articles = new Map<string, { request: Promise<any>; fetchedAt: number }>()
let hoverTimer: ReturnType<typeof setTimeout> | undefined
let hovered: string | undefined

// Params are `<name>-<slug>`; names are hashes with no hyphen.
export function articleName(param: unknown) {
  return String(param || '').split('-')[0]
}

function prefetchArticle(name: string) {
  let entry = articles.get(name)
  articles.delete(name)
  if (!entry || Date.now() - entry.fetchedAt > ARTICLE_MAX_AGE_MS) {
    const request = frappeRequest({ url: 'helpdesk.api.knowledge_base.get_article', method: 'GET', params: { name } })
    request.catch(() => articles.get(name)?.request === request && articles.delete(name))
    entry = { request, fetchedAt: Date.now() }
  }
  articles.set(name, entry)
  if (articles.size > ARTICLE_CACHE_SIZE) articles.delete(articles.keys().next().value)
  return entry.request
}

export function prefetchOnHover(name: string | undefined) {
  // Refires per child crossed; keep the running timer.
  if (name === hovered) return
  hovered = name
  clearTimeout(hoverTimer)
  if (name) hoverTimer = setTimeout(() => prefetchArticle(name), HOVER_DELAY)
}

export function useArticle(name: MaybeRefOrGetter<string>) {
  const article = reactive<{ data: any; error: unknown; loading: boolean }>({
    data: null,
    error: null,
    loading: false,
  })
  watch(
    () => toValue(name),
    async (current) => {
      if (!current) return
      article.loading = true
      try {
        const data = await prefetchArticle(current)
        if (toValue(name) === current) Object.assign(article, { data, error: null })
      } catch (error) {
        if (toValue(name) === current) article.error = error
      } finally {
        if (toValue(name) === current) article.loading = false
      }
    },
    { immediate: true },
  )
  return article
}
