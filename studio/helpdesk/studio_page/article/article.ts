import { computed, watch } from 'vue'
import { useClipboard } from '@vueuse/core'
import { call, dayjs, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { useRecent } from '@app/stores/recent'
import { useSession } from '@app/stores/session'
import { useSettingsModal } from '@app/stores/settings'
import { runAction } from '@app/utils'

const WORDS_PER_MINUTE = 200
const RELATED_LIMIT = 6

export default function setup(context) {
  // `article` is absent on the builder canvas, where the route has no name.
  const { article, articles } = context

  const parsed = computed(() => {
    const dom = new DOMParser().parseFromString(article?.data?.content || '', 'text/html')
    const toc = Array.from(dom.querySelectorAll('h1, h2, h3')).map((heading, index) => {
      heading.id = `section-${index}`
      return { id: heading.id, text: heading.textContent.trim() }
    })
    const words = dom.body.textContent.trim().split(/\s+/).filter(Boolean).length
    const image = dom.querySelector('img')?.getAttribute('src') || null
    return { html: dom.body.innerHTML, toc, words, image }
  })
  const articleHtml = computed(() => parsed.value.html)
  const toc = computed(() => parsed.value.toc)
  const minutes = computed(() => Math.max(1, Math.round(parsed.value.words / WORDS_PER_MINUTE)))
  const readingTime = computed(() =>
    minutes.value === 1 ? __('1 minute to read') : __('{0} minutes to read', [minutes.value]),
  )

  const publishedOn = computed(() => {
    const date = article?.data?.published_on
    return date ? dayjs(date).format('D MMM YYYY') : ''
  })

  const { isPublicKnowledgeBase } = useSession()
  const isPublicArticle = computed(
    () => article?.data?.visibility === 'Public' && isPublicKnowledgeBase.value,
  )

  const currentCategory = computed(() =>
    article?.data?.category
      ? { label: article.data.category_name, route: ROUTES.category(article.data.category) }
      : null,
  )

  const relatedArticles = computed(() =>
    (articles.data || [])
      .filter((row) => row.category === article?.data?.category && row.name !== article.data.name)
      .slice(0, RELATED_LIMIT),
  )

  // `get_public_article` answers with the reader's own vote: '1' like, '2' dislike, '0' none.
  const vote = computed(() => article?.data?.feedback)

  function submitFeedback(value) {
    return runAction(
      async () => {
        await call('helpdesk.api.knowledge_base.vote_on_article', { article: article.data.name, value })
        article.data.feedback = value
      },
      { success: __('Thanks for your feedback!'), fallback: __('Could not submit feedback') },
    )
  }

  // `legacy` falls back to execCommand where the Clipboard API is missing (plain http).
  const { copy } = useClipboard({ legacy: true })
  async function copyLink() {
    await copy(window.location.href)
    toast.success(__('Link copied'))
  }

  // Counted here, not on read: the endpoint is rate limited per article and reader.
  const { rememberArticle } = useRecent()
  watch(
    () => article?.data?.name,
    (name) => {
      if (!name) return
      call('helpdesk.api.knowledge_base.increment_views', { article: name }).catch(() => {})
      rememberArticle({
        name,
        title: article.data.title,
        categoryName: article.data.category_name,
        image: parsed.value.image,
        minutes: minutes.value,
      })
    },
    { immediate: true },
  )

  return {
    ...useSettingsModal(context),
    articleHtml,
    toc,
    readingTime,
    publishedOn,
    currentCategory,
    relatedArticles,
    vote,
    submitFeedback,
    copyLink,
    isPublicArticle,
  }
}
