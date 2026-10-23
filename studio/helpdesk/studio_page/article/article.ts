import { computed, watch } from 'vue'
import { call } from 'frappe-ui'
import { dayjsLocal } from '@helpdesk/shared/timezone'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import {
  addHeadingIds,
  copyPageLink,
  countLabel,
  DATE_FORMATS,
  findArticleHeading,
} from '@helpdesk/shared/utils'
import { useRecent } from '@app/stores/recent'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { saveArticleFeedback } from '@app/components/knowledge_base/articleFeedback'
import { useBottomSheet } from '@app/composables/useDrawer'
import { articleName, prefetchOnHover, useArticle, useKnowledgeBase } from '@app/stores/knowledgeBase'

const RELATED_LIMIT = 5

export default function setup(context) {
  const { route, router } = context
  const article = useArticle(() => articleName(route?.params?.name))
  const { sidebar } = useKnowledgeBase()
  const settings = useKnowledgeBaseHeader(context)

  const parsed = computed(() => {
    const { html, headings } = addHeadingIds(article.data?.content)
    return { html, toc: headings.filter((heading) => heading.level <= 3) }
  })
  const minutes = computed(() => article.data?.minutes)
  const readingTime = computed(() =>
    minutes.value ? countLabel(minutes.value, __('1 minute to read'), __('{0} minutes to read')) : '',
  )

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
  function findHeading(id) {
    return (
      findArticleHeading(id) ||
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
      // `<article>/settings/...`: fixed once the dialog closes.
      if (router.currentRoute.value.params.settings !== undefined) return
      // Resolved, so slugs compare in the router's own encoding.
      const path = router.resolve(ROUTES.article(article.data)).path
      // The route's hash is decoded; `location.hash` would be encoded twice.
      if (current !== path) router.replace({ path, hash: router.currentRoute.value.hash })
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
      else document.querySelector('[data-component-id="container-article-scroll"]')?.scrollTo({ top: 0 })
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
    drawer: useBottomSheet(route),
    sidebar,
    article,
    prefetchOnHover,
    parsed,
    readingTime,
    publishedOn,
    relatedArticles,
    submitFeedback,
    copyPageLink,
    isPublicArticle,
    isCurrentArticle,
  }
}
