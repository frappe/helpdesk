import { computed, ref, watch } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'

const ARTICLE_LIMIT = 5

export default function setup(context) {
  const { articles, categories } = context

  const fewCategories = computed(() => {
    const rows = categories.data || []
    return rows.length === 1 || rows.length === 2 ? rows : []
  })
  const hasCategoryPicker = computed(() => fewCategories.value.length === 2)
  const pickedName = ref(null)
  const focusCategory = computed(
    () => fewCategories.value.find((row) => row.name === pickedName.value) || fewCategories.value[0] || null,
  )

  function pickCategory(name) {
    pickedName.value = name
  }

  function articleCount(category) {
    return category.article_count === 1 ? __('1 article') : __('{0} articles', [category.article_count])
  }

  const isLoneCategory = computed(() => Boolean(focusCategory.value && !hasCategoryPicker.value))

  // Waits for the categories: an earlier fetch could land after the right one.
  const sort = ref('latest')
  watch([sort, focusCategory, () => categories.data], ([value, category, loaded]) => {
    if (!loaded) return
    if (!category) return articles.fetch({ limit: ARTICLE_LIMIT, sort: value })
    const limit = isLoneCategory.value ? 0 : ARTICLE_LIMIT
    articles.fetch({ category: category.name, limit, sort: value })
  }, { immediate: true })

  return {
    ...useSettingsModal(context),
    sort,
    focusCategory,
    hasCategoryPicker,
    isLoneCategory,
    articleCount,
    pickCategory,
  }
}
