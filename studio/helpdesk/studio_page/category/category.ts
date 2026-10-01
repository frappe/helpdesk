import { computed, ref } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { timeAgo } from '@helpdesk/shared/utils'
import { useSettingsModal } from '@app/stores/settings'
import { matchesQuery } from '@app/utils'

export default function setup(context) {
  const { category, articles, route } = context

  const query = ref('')

  const filteredArticles = computed(() =>
    (articles.data || []).filter((article) => matchesQuery(query.value, article.title, article.excerpt)),
  )

  const categoryName = computed(() => category.data?.category_name || route.params.category)
  const categoryDescription = computed(
    () => category.data?.description || __('Find answers to common {0} questions.', [categoryName.value]),
  )

  return {
    ...useSettingsModal(context),
    query,
    filteredArticles,
    categoryName,
    categoryDescription,
    timeAgo,
  }
}
