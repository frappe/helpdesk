import { computed } from 'vue'
import { useStorage } from '@vueuse/core'

const SEARCH_LIMIT = 5
const ARTICLE_LIMIT = 3

export type RecentArticle = {
  name: string
  title: string
  categoryName?: string
  image?: string | null
  minutes?: number
}

// Per browser, as DocSearch does, so it works for guests.
const searches = useStorage<string[]>('helpdesk-kb-recent-searches', [])
const articles = useStorage<RecentArticle[]>('helpdesk-kb-recent-articles', [])

function remember<T>(list: T[], item: T, same: (row: T) => boolean, limit: number) {
  return [item, ...list.filter((row) => !same(row))].slice(0, limit)
}

export function useRecent() {
  function rememberSearch(text: string) {
    const query = text.trim()
    if (!query) return
    const key = query.toLowerCase()
    searches.value = remember(searches.value, query, (row) => row.toLowerCase() === key, SEARCH_LIMIT)
  }

  function forgetSearch(text: string) {
    searches.value = searches.value.filter((row) => row !== text)
  }

  function clearSearches() {
    searches.value = []
  }

  function rememberArticle(article: RecentArticle) {
    articles.value = remember(articles.value, article, (row) => row.name === article.name, ARTICLE_LIMIT)
  }

  return {
    recentSearches: computed(() => searches.value),
    recentArticles: computed(() => articles.value),
    rememberSearch,
    forgetSearch,
    clearSearches,
    rememberArticle,
  }
}
