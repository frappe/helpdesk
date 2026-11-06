import { computed, watch } from 'vue'
import { useStorage } from '@vueuse/core'
import { useSession } from '@app/stores/session'

const ARTICLE_LIMIT = 3

type RecentArticle = {
  name: string
  title: string
  title_slug?: string
  categoryName?: string
  minutes?: number
}

// Per user, so a shared machine doesn't leak history.
const { config } = useSession()
const user = () => config.value?.session_user || 'Guest'
const articles = useStorage<RecentArticle[]>(() => `helpdesk-kb-recent-articles:${user()}`, [])

// Held until the session loads, so it lands in the right user's list.
let pendingArticle: RecentArticle | undefined
watch(config, () => pendingArticle && addArticle(pendingArticle))

function addArticle(article: RecentArticle) {
  pendingArticle = config.value ? undefined : article
  if (pendingArticle) return
  articles.value = [article, ...articles.value.filter((row) => row.name !== article.name)].slice(0, ARTICLE_LIMIT)
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
