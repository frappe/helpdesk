import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useBottomSheet } from '@app/composables/useDrawer'
import { countLabel } from '@helpdesk/shared/utils'
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
  // `articles` is capped server side.
  const articleCount = computed(() => countLabel(category.value?.article_count, __('1 article'), __('{0} articles')))

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
  }
}
