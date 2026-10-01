import { computed, ref, watch } from 'vue'
import { call, dayjs, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { ROUTES } from '@app/routes'
import { useSession } from '@app/stores/session'
import { useSettingsModal } from '@app/stores/settings'
import { matchesQuery, runAction } from '@app/utils'

const WORDS_PER_MINUTE = 200
const RELATED_LIMIT = 6

export default function setup(context) {
  // `article` is absent on the builder canvas, where the route has no name.
  const { article, articles, categories } = context

  // The headings get ids here so the table of contents can scroll to them.
  const parsed = computed(() => {
    const dom = new DOMParser().parseFromString(article?.data?.content || '', 'text/html')
    const toc = Array.from(dom.querySelectorAll('h1, h2, h3')).map((heading, index) => {
      heading.id = `section-${index}`
      return { id: heading.id, text: heading.textContent.trim() }
    })
    const words = dom.body.textContent.trim().split(/\s+/).filter(Boolean).length
    return { html: dom.body.innerHTML, toc, words }
  })
  const articleHtml = computed(() => parsed.value.html)
  const toc = computed(() => parsed.value.toc)
  const readingTime = computed(() => {
    const minutes = Math.max(1, Math.round(parsed.value.words / WORDS_PER_MINUTE))
    return minutes === 1 ? __('1 minute to read') : __('{0} minutes to read', [minutes])
  })

  const publishedOn = computed(() => {
    const date = article?.data?.published_on
    return date ? dayjs(date).format('D MMM YYYY') : ''
  })

  // Only a page anyone can open can be handed to an assistant by URL.
  const { isPublicKnowledgeBase } = useSession()
  const isPublicArticle = computed(
    () => article?.data?.visibility === 'Public' && isPublicKnowledgeBase.value,
  )

  const currentCategory = computed(() =>
    article?.data?.category
      ? { label: article.data.category_name, route: ROUTES.category(article.data.category) }
      : null,
  )

  // Sidebar: one node per category, its articles as leaves. A category name match keeps
  // all of its articles; otherwise only the matching titles survive.
  const sidebarQuery = ref('')
  const categoryTree = computed(() =>
    (categories.data || [])
      .map((category) => {
        const label = category.category_name || category.name
        const wholeCategory = matchesQuery(sidebarQuery.value, label)
        const children = (articles.data || [])
          .filter((row) => row.category === category.name)
          .filter((row) => wholeCategory || matchesQuery(sidebarQuery.value, row.title))
          .map((row) => ({ name: row.name, label: row.title, isActive: row.name === article?.data?.name }))
        return { name: category.name, label, children, isCurrent: children.some((child) => child.isActive) }
      })
      .filter((category) => !sidebarQuery.value || category.children.length),
  )

  // Open on the category being read until the reader toggles it; a search opens them all.
  const toggled = ref({})
  function isExpanded(name) {
    if (sidebarQuery.value) return true
    if (name in toggled.value) return toggled.value[name]
    return categoryTree.value.find((category) => category.name === name)?.isCurrent || false
  }
  function toggleCategory(name) {
    toggled.value = { ...toggled.value, [name]: !isExpanded(name) }
  }

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

  async function copyLink() {
    await navigator.clipboard.writeText(window.location.href)
    toast.success(__('Link copied'))
  }

  // Counted here, not on read: the endpoint is rate limited per article and reader.
  watch(
    () => article?.data?.name,
    (name) => name && call('helpdesk.api.knowledge_base.increment_views', { article: name }).catch(() => {}),
    { immediate: true },
  )

  return {
    ...useSettingsModal(context),
    articleHtml,
    toc,
    readingTime,
    publishedOn,
    currentCategory,
    sidebarQuery,
    categoryTree,
    isExpanded,
    toggleCategory,
    relatedArticles,
    vote,
    submitFeedback,
    copyLink,
    isPublicArticle,
  }
}
