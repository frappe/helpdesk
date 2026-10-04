import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'
import { useDrawer } from '@app/composables/useDrawer'
import { countLabel } from '@app/utils'

export default function setup(context) {
  const { category, articles, categories, route } = context

  const categoryName = computed(() => category.data?.category_name || route.params.category)
  const categoryDescription = computed(
    () => category.data?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )
  // `articles` is capped server side; the categories list carries the full count.
  const total = computed(
    () =>
      categories.data?.find((row) => row.name === route.params.category)?.article_count ??
      articles.data?.length ??
      0,
  )
  const articleCount = computed(() => countLabel(total.value, __('1 article'), __('{0} articles')))

  return {
    ...useSettingsModal(context),
    drawer: useDrawer(route),
    categoryName,
    categoryDescription,
    articleCount,
  }
}
