import { ref, watch } from 'vue'
import { useSettingsModal } from '@app/stores/settings'

const ARTICLE_LIMIT = 5

export default function setup(context) {
  const { articles } = context

  // Re-asked of the server, not re-sorted here: the list holds only the first few.
  const sort = ref('latest')
  watch(sort, (value) => articles.fetch({ limit: ARTICLE_LIMIT, sort: value }))

  return { ...useSettingsModal(context), sort }
}
