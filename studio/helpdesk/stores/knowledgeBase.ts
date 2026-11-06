import { reactive, ref, toValue, watch, type MaybeRefOrGetter } from 'vue'
import { createResource, frappeRequest } from 'frappe-ui'
import { findArticleHeading } from '@helpdesk/shared/utils'

// Module-level, not `cache`: what a reader sees depends on who they are.
const sidebar = createResource({
  url: 'helpdesk.api.knowledge_base.get_kb_sidebar',
  method: 'GET',
})

// Two or four cards only fill their rows in two columns.
export const homeCategoryColumns = (count: number) => (count === 2 || count === 4 ? 2 : 3)

export function useKnowledgeBase() {
  if (!sidebar.data && !sidebar.loading) sidebar.fetch()
  return { sidebar }
}

// Survives the sidebar's remount on each page.
export const sidebarState = {
  query: ref(''),
  openName: ref<string | null>(null),
  openSubName: ref<string | null>(null),
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
  // `settled` names the Article that `data` or `error` answers.
  const article = reactive<{ data: any; error: unknown; loading: boolean; settled: string }>({
    data: null,
    error: null,
    loading: false,
    settled: '',
  })
  watch(
    () => toValue(name),
    async (current) => {
      Object.assign(article, { error: null, settled: '' })
      if (!current) return Object.assign(article, { data: null, loading: false, settled: '' })
      article.loading = true
      try {
        const data = await prefetchArticle(current)
        if (toValue(name) === current) Object.assign(article, { data, error: null })
      } catch (error) {
        if (toValue(name) === current) article.error = error
      } finally {
        if (toValue(name) === current) Object.assign(article, { loading: false, settled: current })
      }
    },
    { immediate: true },
  )
  return article
}

export function scrollToHash(tries = 40) {
  const heading = findHeading(decodeHash())
  if (heading) heading.scrollIntoView()
  else if (tries) setTimeout(() => scrollToHash(tries - 1), 50)
}

// A hand-typed `#100%` is not valid percent-encoding.
function decodeHash() {
  try {
    return decodeURIComponent(location.hash.slice(1))
  } catch {
    return location.hash.slice(1)
  }
}

// Old desk KB ids kept edge dashes: "What's new?" was `what-s-new-`.
function findHeading(id: string) {
  return (
    findArticleHeading(id) ||
    [...document.querySelectorAll('h2, h3, h4, h5, h6')].find(
      (heading) => heading.textContent.trim().replace(/[^a-z0-9]+/gi, '-').toLowerCase() === id,
    )
  )
}
