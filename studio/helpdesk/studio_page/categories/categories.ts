import { computed, ref } from 'vue'
import { matchesQuery } from '@helpdesk/shared/utils'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useBottomSheet } from '@app/composables/useDrawer'
import { useRememberedCount } from '@app/composables/useRememberedCount'
import { useKnowledgeBase } from '@app/stores/knowledgeBase'

export default function setup(context) {
  const { sidebar } = useKnowledgeBase()
  const search = ref('')
  // Subcategories open from their parent's page.
  const topCategories = computed(() => context.categories.data?.filter((row) => !row.parent_article_category))
  const matches = (row) => matchesQuery(search.value, row.category_name, row.description)
  // A parent is shown when it or one of its subcategories matches.
  const shownCategories = computed(() =>
    (topCategories.value || []).filter(
      (row) =>
        matches(row) ||
        context.categories.data.some((sub) => sub.parent_article_category === row.name && matches(sub)),
    ),
  )
  // Five rows fill the page; more would only scroll.
  const skeletonCount = Math.min(
    useRememberedCount('helpdesk-kb-categories', () => topCategories.value?.length, 15),
    15,
  )
  return {
    ...useKnowledgeBaseHeader(context),
    drawer: useBottomSheet(context.route),
    sidebar,
    search,
    shownCategories,
    skeletonCount,
  }
}
