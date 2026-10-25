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
  const shownCategories = computed(() =>
    (topCategories.value || []).filter((row) => matchesQuery(search.value, row.category_name, row.description)),
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
