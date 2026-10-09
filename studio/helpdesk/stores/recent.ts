import { computed, watch } from 'vue'
import { useStorage } from '@vueuse/core'
import { useSession } from '@app/stores/session'

const ARTICLE_LIMIT = 3

export type RecentArticle = {
  name: string
  title: string
  categoryName?: string
  image?: string | null
  minutes?: number
}

// Per browser and user, so the next person at a shared machine starts clean.
const { config } = useSession()
const user = () => config.value?.session_user || 'Guest'
const articles = useStorage<RecentArticle[]>(() => `helpdesk-kb-recent-articles:${user()}`, [])
try {
  localStorage.removeItem('helpdesk-kb-recent-searches')
  localStorage.removeItem('helpdesk-kb-recent-articles')
} catch {}

function remember<T>(list: T[], item: T, same: (row: T) => boolean, limit: number) {
  return [item, ...list.filter((row) => !same(row))].slice(0, limit)
}

// An article opened before the session is known waits for it, so it lands in the right user's list.
let pendingArticle: RecentArticle | undefined
watch(config, () => pendingArticle && addArticle(pendingArticle))

function addArticle(article: RecentArticle) {
  pendingArticle = config.value ? undefined : article
  if (pendingArticle) return
  articles.value = remember(articles.value, article, (row) => row.name === article.name, ARTICLE_LIMIT)
}

export function useRecent() {
  function forgetArticle(name: string) {
    articles.value = articles.value.filter((row) => row.name !== name)
  }

  return {
    recentArticles: computed(() => articles.value),
    rememberArticle: addArticle,
    forgetArticle,
  }
}
