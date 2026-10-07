import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'
import { useKbHeader } from '@app/composables/useKbHeader'
import { useDrawer } from '@app/composables/useDrawer'
import { countLabel } from '@app/utils'

export default function setup(context) {
  const { articles, categories, route } = context

  const category = computed(() => categories.data?.find((row) => row.name === route.params.category))
  // The list holds only categories with an article this reader may see.
  const notFound = computed(() => Boolean(categories.data) && !category.value)
  const categoryName = computed(() => category.value?.category_name || route.params.category)
  const categoryDescription = computed(
    () => category.value?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )
  // `articles` is capped server side; the categories list carries the full count.
  const total = computed(() => category.value?.article_count ?? articles.data?.length ?? 0)
  const articleCount = computed(() => countLabel(total.value, __('1 article'), __('{0} articles')))

  return {
    ...useSettingsModal(context),
    ...useKbHeader(context),
    drawer: useDrawer(route),
    category,
    notFound,
    categoryName,
    categoryDescription,
    articleCount,
  }
}
