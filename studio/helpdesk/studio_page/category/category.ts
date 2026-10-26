import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useBottomSheet } from '@app/composables/useDrawer'
import { countLabel } from '@helpdesk/shared/utils'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
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
  // `articles` is capped server side; the count includes Subcategories.
  const countText = (count) => countLabel(count, __('1 article'), __('{0} articles'))
  const articleCount = computed(() => countText(category.value?.article_count))

  // Sidebar rows come sorted by `category_name`.
  const subcategories = computed(() =>
    (sidebar.data || []).filter((row) => row.parent_article_category === route.params.category),
  )
  const subcategoryCount = computed(() =>
    countLabel(subcategories.value.length, __('1 subcategory'), __('{0} subcategories')),
  )
  const sections = computed(() =>
    subcategories.value
      .filter((row) => context.subcategoryArticles.data?.[row.name]?.length)
      .map((row) => ({ name: row.name, category: row, articles: context.subcategoryArticles.data[row.name] })),
  )
  const loaded = computed(
    () => Boolean(context.articles.data && sidebar.data && context.subcategoryArticles.data),
  )
  const categoryIcon = computed(() => category.value?.icon || 'lucide-folder')
  const parentCategory = computed(
    () => sidebar.data?.find((row) => row.name === category.value?.parent_article_category) || null,
  )
  const breadcrumbs = computed(() => [
    { label: __('Help'), route: ROUTES.home },
    ...(parentCategory.value
      ? [{ label: parentCategory.value.category_name, route: ROUTES.category(parentCategory.value.name) }]
      : []),
    { label: categoryName.value },
  ])

  return {
    ...useKnowledgeBaseHeader(context),
    drawer: useBottomSheet(route),
    sidebar,
    prefetchOnHover,
    category,
    notFound,
    categoryName,
    categoryDescription,
    articleCount,
    subcategories,
    subcategoryCount,
    sections,
    loaded,
    categoryIcon,
    parentCategory,
    breadcrumbs,
  }
}
