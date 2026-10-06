import { useSettingsModal } from '@app/stores/settings'
import { useKbHeader } from '@app/composables/useKbHeader'

// Every category, for when the home page shows only the pinned ones.
export default function setup(context) {
  return { ...useSettingsModal(context), ...useKbHeader(context) }
}
