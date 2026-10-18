import { computed, watch } from 'vue'
import { call, dayjsLocal } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { addHeadingIds, addOutlineIds, articleMeta, copyPageLink, countLabel, DATE_FORMATS } from '@helpdesk/shared/utils'
import { useRecent } from '@app/stores/recent'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { saveArticleFeedback } from '@app/components/knowledge_base/articleFeedback'
import { useDrawer } from '@app/composables/useDrawer'
import { articleName, prefetchOnHover, useArticle, useKnowledgeBase } from '@app/stores/knowledgeBase'

const RELATED_LIMIT = 5

export default function setup(context) {
  const { route, router } = context
  const article = useArticle(() => articleName(route?.params?.name))
  const { sidebar } = useKnowledgeBase()
  const settings = useKnowledgeBaseHeader(context)

  const parsed = computed(() => {
    const { html, headings } = addHeadingIds(article.data?.content)
    if (headings.length) return { html, toc: headings.filter((heading) => heading.level <= 3) }
    const outline = addOutlineIds(html)
    return { html: outline.html, toc: outline.sections }
  })
  const minutes = computed(() => article.data?.minutes)
  const readingTime = computed(() =>
    minutes.value ? countLabel(minutes.value, __('1 minute to read'), __('{0} minutes to read')) : '',
  )
  const eyebrow = computed(() => articleMeta(article.data?.category_name, minutes.value))

  const publishedOn = computed(() => {
    const date = article.data?.published_on
    return date ? dayjsLocal(date).format(DATE_FORMATS.short) : ''
  })

  const isPublicArticle = computed(
    () => article.data?.visibility === 'Public' && settings.isPublicKnowledgeBase.value,
  )

  const relatedArticles = computed(() =>
    (sidebar.data?.find((category) => category.name === article.data?.category)?.articles || [])
      .filter((row) => row.name !== article.data.name)
      .slice(0, RELATED_LIMIT),
  )

  // Pre-slug links carry the bare name.
  function isCurrentArticle(routeName) {
    const name = article.data?.name
    return Boolean(name) && (routeName === name || routeName?.startsWith(`${name}-`))
  }

  function scrollToHash(tries = 40) {
    const heading = findHeading(decodeURIComponent(location.hash.slice(1)))
    if (heading) heading.scrollIntoView()
    else if (tries) setTimeout(() => scrollToHash(tries - 1), 50)
  }

  // Old desk KB ids kept edge dashes: "What's new?" was `what-s-new-`.
  function findHeading(id) {
    return (
      document.getElementById(id) ||
      [...document.querySelectorAll('h2, h3, h4, h5, h6')].find(
        (heading) => heading.textContent.trim().replace(/[^a-z0-9]+/gi, '-').toLowerCase() === id,
      )
    )
  }

  // The reader's own feedback: 1 like, 2 dislike, 0 none.
  function submitFeedback(answer) {
    const { name, feedback } = article.data
    return saveArticleFeedback(name, feedback, answer, (value) => (article.data.feedback = value))
  }

  // Replacing while the navigation is pending would cancel it.
  watch(
    () => [article.data?.name, router.currentRoute.value.path],
    ([name, current]) => {
      if (!name || !isCurrentArticle(router.currentRoute.value.params.name)) return
      // Resolved, so slugs compare in the router's own encoding.
      const path = router.resolve(ROUTES.article(article.data)).path
      if (current !== path) router.replace({ path, hash: location.hash })
    },
    { immediate: true },
  )

  // The endpoint counts a reader once per article an hour.
  const { rememberArticle } = useRecent()
  watch(
    () => article.data?.name,
    (name) => {
      if (!name) return
      // Own scroll panel keeps its place; the hash target renders after fetch.
      if (location.hash) scrollToHash()
      else document.querySelector('[data-component-id="container-gi1caqqm1"]')?.scrollTo({ top: 0 })
      call('helpdesk.api.knowledge_base.increment_views', { article: name }).catch(() => {})
      rememberArticle({
        name,
        title: article.data.title,
        title_slug: article.data.title_slug,
        categoryName: article.data.category_name,
        minutes: minutes.value,
      })
    },
    { immediate: true },
  )

  return {
    ...settings,
    drawer: useDrawer(route),
    sidebar,
    article,
    prefetchOnHover,
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
