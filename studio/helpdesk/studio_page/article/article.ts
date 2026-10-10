import { computed, watch } from 'vue'
import { call, dayjsLocal } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { addHeadingIds } from '@helpdesk/shared/utils'
import { useRecent } from '@app/stores/recent'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { articleMeta, copyPageLink, countLabel, DATE_FORMATS } from '@app/utils'
import { saveArticleFeedback } from '@app/components/knowledge_base/articleFeedback'
import { useDrawer } from '@app/composables/useDrawer'

const RELATED_LIMIT = 6

export default function setup(context) {
  // `article` is absent on the builder canvas, where the route has no name.
  const { article, articles, router } = context
  const settings = useKnowledgeBaseHeader(context)

  const parsed = computed(() => {
    const { html, headings } = addHeadingIds(article?.data?.content)
    return { html, toc: headings.filter((heading) => heading.level <= 3) }
  })
  const minutes = computed(() => article?.data?.minutes)
  const readingTime = computed(() =>
    minutes.value ? countLabel(minutes.value, __('1 minute to read'), __('{0} minutes to read')) : '',
  )
  const eyebrow = computed(() => articleMeta(article?.data?.category_name, minutes.value))

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

  // ponytail: polls ~2s for the editor to render the body; a hook from PortalArticleBody if that ever runs short.
  function scrollToHash(tries = 40) {
    const heading = document.getElementById(decodeURIComponent(location.hash.slice(1)))
    if (heading) heading.scrollIntoView()
    else if (tries) setTimeout(() => scrollToHash(tries - 1), 50)
  }

  // `get_public_article` answers with the reader's own feedback: 1 like, 2 dislike, 0 none.
  function submitFeedback(answer) {
    const { name, feedback } = article.data
    return saveArticleFeedback(name, feedback, answer, (value) => (article.data.feedback = value))
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
      // The heading renders after the fetch, so the browser's own jump to the hash found nothing.
      if (location.hash) scrollToHash()
      else document.querySelector('[data-component-id="container-gi1caqqm1"]')?.scrollTo({ top: 0 })
      call('helpdesk.api.knowledge_base.increment_views', { article: name }).catch(() => {})
      rememberArticle({
        name,
        title: article.data.title,
        categoryName: article.data.category_name,
        minutes: minutes.value,
      })
    },
    { immediate: true },
  )

  return {
    ...settings,
    drawer: useDrawer(context.route),
    parsed,
    readingTime,
    eyebrow,
    publishedOn,
    relatedArticles,
    submitFeedback,
    copyPageLink,
    isPublicArticle,
    isCurrentArticle,
  }
}
