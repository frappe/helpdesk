import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'

export default function setup(context) {
  const { category, articles, route } = context

  const categoryName = computed(() => category.data?.category_name || route.params.category)
  const categoryDescription = computed(
    () => category.data?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )
  const articleCount = computed(() => {
    const count = articles.data?.length || 0
    return count === 1 ? __('1 article') : __('{0} articles', [count])
  })

  return {
    ...useSettingsModal(context),
    categoryName,
    categoryDescription,
    articleCount,
  }
}
