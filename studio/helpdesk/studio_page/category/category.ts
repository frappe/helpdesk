import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useBottomSheet } from '@app/composables/useDrawer'
import { useMoreArticles } from '@app/composables/useMoreArticles'
import { dayjsLocal } from '@helpdesk/shared/timezone'
import { countLabel, DATE_FORMATS } from '@helpdesk/shared/utils'
import { prefetchOnHover, useKnowledgeBase } from '@app/stores/knowledgeBase'

export default function setup(context) {
  const { route } = context
  const { sidebar } = useKnowledgeBase()

  const category = computed(() => sidebar.data?.find((row) => row.name === route.params.category))
  // The sidebar omits categories this reader cannot see.
  const notFound = computed(() => Boolean(sidebar.data) && !category.value)
  const categoryName = computed(() => category.value?.category_name)
  const categoryDescription = computed(
    () => category.value?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )
  // `articles` is one page; the count includes Subcategories.
  const countText = (count) => countLabel(count, __('1 article'), __('{0} articles'))
  const articleCount = computed(() => countText(category.value?.article_count))

  // Sidebar rows come sorted by `category_name`.
  const subcategories = computed(() =>
    (sidebar.data || []).filter((row) => row.parent_article_category === route.params.category),
  )
  // Newest readable article in the category or its Subcategories.
  const lastUpdated = computed(() => {
    const date = category.value?.last_updated
    return date ? __('Last updated on {0}', [dayjsLocal(date).format(DATE_FORMATS.short)]) : ''
  })
  const sections = computed(() =>
    subcategories.value
      .filter((row) => context.subcategoryArticles.data?.[row.name]?.length)
      .map((row) => ({ name: row.name, category: row, articles: context.subcategoryArticles.data[row.name] })),
  )
  // As many rows as the category's own articles, so the skeleton doesn't fill the page.
  const skeletonRows = computed(() => Math.min(Math.max(category.value?.articles?.length ?? 3, 1), 8))
  // Both fetches must settle, or a switch shows the new list with old sections; a failed section fetch still counts.
  const loaded = computed(
    () =>
      !context.articles.loading &&
      !context.subcategoryArticles.loading &&
      Boolean(context.articles.data && sidebar.data && (context.subcategoryArticles.data || context.subcategoryArticles.error)),
  )
  // Without these the page has nothing to show; a section fetch failing only drops its cards.
  const loadFailed = computed(() => Boolean(sidebar.error || context.articles.error))

  return {
    ...useKnowledgeBaseHeader(context),
    drawer: useBottomSheet(route),
    sidebar,
    prefetchOnHover,
    moreArticles: useMoreArticles(context.articles, () => route.params.category),
    category,
    notFound,
    categoryName,
    categoryDescription,
    articleCount,
    subcategories,
    lastUpdated,
    sections,
    loaded,
    loadFailed,
    skeletonRows,
  }
}
