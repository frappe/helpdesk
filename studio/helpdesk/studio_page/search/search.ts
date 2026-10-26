import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { useBottomSheet } from '@app/composables/useDrawer'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { useKnowledgeBase } from '@app/stores/knowledgeBase'

export default function setup(context) {
  const { route } = context
  const { sidebar } = useKnowledgeBase()

  const tabTitle = computed(() => {
    const query = String(route.query.q || '').trim()
    return query ? `${query} – ${__('Search')}` : __('Search')
  })

  return {
    ...useKnowledgeBaseHeader(context),
    drawer: useBottomSheet(route),
    sidebar,
    tabTitle,
    breadcrumbs: computed(() => [{ label: __('Help'), route: ROUTES.home }, { label: __('Search') }]),
  }
}
