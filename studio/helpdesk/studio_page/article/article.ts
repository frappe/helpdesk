import { computed, watch } from 'vue'
import { useClipboard } from '@vueuse/core'
import { call, dayjsLocal, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { useRecent } from '@app/stores/recent'
import { usePageTitle } from '@app/stores/session'
import { useSettingsModal } from '@app/stores/settings'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { countLabel, DATE_FORMATS, runAction } from '@app/utils'
import { useDrawer } from '@app/composables/useDrawer'

const WORDS_PER_MINUTE = 200
const RELATED_LIMIT = 6

export default function setup(context) {
  // `article` is absent on the builder canvas, where the route has no name.
  const { article, articles, router } = context
  const settings = useSettingsModal(context)
  usePageTitle(() => (article?.error ? __('Article not found') : article?.data?.title))

  const parsed = computed(() => {
    const dom = new DOMParser().parseFromString(article?.data?.content || '', 'text/html')
    const toc = Array.from(dom.querySelectorAll('h1, h2, h3')).map((heading, index) => {
      heading.id = `section-${index}`
      return { id: heading.id, text: heading.textContent.trim(), level: Number(heading.tagName[1]) }
    })
    const words = dom.body.textContent.trim().split(/\s+/).filter(Boolean).length
    const image = dom.querySelector('img')?.getAttribute('src') || null
    return { html: dom.body.innerHTML, toc, words, image }
  })
  const minutes = computed(() => Math.max(1, Math.round(parsed.value.words / WORDS_PER_MINUTE)))
  const readingTime = computed(() => countLabel(minutes.value, __('1 minute to read'), __('{0} minutes to read')))
  const eyebrow = computed(() =>
    [article?.data?.category_name, countLabel(minutes.value, __('1 min read'), __('{0} min read'))]
      .filter(Boolean)
      .join(' · '),
  )

  const publishedOn = computed(() => {
    const date = article?.data?.published_on
    return date ? dayjsLocal(date).format(DATE_FORMATS.short) : ''
  })

  const isPublicArticle = computed(
    () => article?.data?.visibility === 'Public' && settings.isPublicKnowledgeBase.value,
  )

  const relatedArticles = computed(() =>
    (articles.data || [])
      .filter((row) => row.category === article?.data?.category && row.name !== article.data.name)
      .slice(0, RELATED_LIMIT),
  )

  // The route's name is `<name>-<title slug>`, or the bare name in links from before slugs.
  function isCurrentArticle(routeName) {
    const name = article?.data?.name
    return Boolean(name) && (routeName === name || routeName?.startsWith(`${name}-`))
  }

  // `get_public_article` answers with the reader's own feedback: '1' like, '2' dislike, '0' none.
  function submitFeedback(value) {
    return runAction(
      async () => {
        await call('helpdesk.api.knowledge_base.set_article_feedback', { article: article.data.name, value })
        article.data.feedback = value
      },
      { success: __('Thanks for your feedback!'), fallback: __('Could not submit feedback') },
    )
  }

  // `legacy`: execCommand fallback where the Clipboard API is missing (plain http).
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
      // Resolved, so a slug in another script compares in the router's own encoding.
      const path = router.resolve(ROUTES.article(article.data)).path
      if (router.currentRoute.value.path !== path) router.replace({ path, hash: location.hash })
      // The article scrolls in its own panel, which keeps its place from one article to the next.
      if (!location.hash) document.querySelector('[data-component-id="container-gi1caqqm1"]')?.scrollTo({ top: 0 })
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
    ...settings,
    ...useKnowledgeBaseHeader(context),
    drawer: useDrawer(context.route),
    parsed,
    readingTime,
    eyebrow,
    publishedOn,
    relatedArticles,
    submitFeedback,
    copyLink,
    isPublicArticle,
    isCurrentArticle,
    articleRoute: ROUTES.article,
  }
}
