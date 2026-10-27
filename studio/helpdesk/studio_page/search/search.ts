import { computed } from 'vue'
import { __ } from '@helpdesk/shared/translation'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'

export default function setup(context) {
  const { route } = context

  const tabTitle = computed(() => {
    const query = String(route.query.q || '').trim()
    return query ? `${query} – ${__('Search')}` : __('Search')
  })

  return {
    ...useKnowledgeBaseHeader(context),
    tabTitle,
  }
}
