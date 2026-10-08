import { __ } from '@helpdesk/shared/translation'
import { useSettingsModal } from '@app/stores/settings'
import { useKnowledgeBaseHeader } from '@app/composables/useKnowledgeBaseHeader'
import { usePageTitle } from '@app/stores/session'

// Every category, for when the home page shows only the pinned ones.
export default function setup(context) {
  usePageTitle(() => __('All categories'))
  return { ...useSettingsModal(context), ...useKnowledgeBaseHeader(context) }
}
