import { computed, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import { dayjsLocal } from '@helpdesk/shared/timezone'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import {
  addHeadingIds,
  copyPageLink,
  countLabel,
  DATE_FORMATS,
} from '@helpdesk/shared/utils'
import { useRecent } from '@app/stores/recent'
import { holdDuring } from '@app/composables/docsResults'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { saveArticleFeedback } from '@app/components/knowledge_base/articleFeedback'
import { useBottomSheet } from '@app/composables/useDrawer'
import {
  articleName,
  prefetchOnHover,
  scrollToHash,
  useArticle,
  useKnowledgeBase,
} from '@app/stores/knowledgeBase'
import { useSession } from '@app/stores/session'
import { decodePath, pagePath } from '@app/stores/settings/core'

const RELATED_LIMIT = 5

export default function setup(context) {
  const { route, router } = context
  const session = useSession()
  const hasDocsSource = computed(() => Boolean(session.config.value?.docs_source_url))
  const isMultiSegment = computed(() => String(route?.params?.name).includes('/'))
  const lookupName = computed(() =>
    hasDocsSource.value && isMultiSegment.value ? '' : articleName(route?.params?.name),
  )
  const article = useArticle(lookupName)
  // A flat route's lookup holds the last view, so only an Article ends a Docs page.
  const isLookingUp = () => article.settled !== lookupName.value
  const isDocsPage = holdDuring(
    isLookingUp,
    () => hasDocsSource.value && (isMultiSegment.value || Boolean(article.error)),
  )
  // The alias cuts `name` short at `/settings`, so use the path.
  const docsRoute = holdDuring(isLookingUp, () => decodePath(pagePath(route)).replace(/^\/articles\//, ''))
  // Only the config tells a missing Article from a Docs page.
  const isConfigSettled = ref(false)
  session.loadSession().then(() => (isConfigSettled.value = true))
  const isArticleMissing = computed(() => Boolean(article.error) && isConfigSettled.value && !hasDocsSource.value)
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

  // Same Subcategory first, then its parent's own Articles.
  const relatedArticles = computed(() => {
    const { category, parent_article_category, name } = article.data || {}
    const articlesOf = (categoryName) => sidebar.data?.find((row) => row.name === categoryName)?.articles || []
    return [...articlesOf(category), ...articlesOf(parent_article_category)]
      .filter((row) => row.name !== name)
      .slice(0, RELATED_LIMIT)
  })

  // Pre-slug links carry the bare name.
  function isCurrentArticle(routeName) {
    const name = article.data?.name
    return Boolean(name) && (routeName === name || routeName?.startsWith(`${name}-`))
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
        categoryName: article.data.category_label,
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
    isDocsPage,
    docsRoute,
    isArticleMissing,
  }
}
