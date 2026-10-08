import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useDrawer } from '@app/composables/useDrawer'
import { countLabel } from '@app/utils'
import { usePageTitle } from '@app/stores/session'
import { ROUTES } from '@app/routes'

export default function setup(context) {
  const { categories, route } = context

  const category = computed(() => categories.data?.find((row) => row.name === route.params.category))
  // The list holds only categories with an article this reader may see.
  const notFound = computed(() => Boolean(categories.data) && !category.value)
  const categoryName = computed(() => category.value?.category_name)
  const categoryDescription = computed(
    () => category.value?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )
  // `articles` is capped server side; the categories list carries the full count.
  const articleCount = computed(() => countLabel(category.value?.article_count, __('1 article'), __('{0} articles')))
  usePageTitle(() => (notFound.value ? __('Category not found') : categoryName.value))

  return {
    ...useSettingsModal(context),
    ...useKnowledgeBaseHeader(context),
    drawer: useDrawer(route),
    category,
    notFound,
    categoryName,
    categoryDescription,
    articleCount,
    articleRoute: ROUTES.article,
  }
}
