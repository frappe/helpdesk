import { ref } from 'vue'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'
import { useKbHeader } from '@app/composables/useKbHeader'
import { useArticleSearch } from '@app/composables/useArticleSearch'

export default function setup(context) {
  const query = ref(String(context.route.query.q || ''))
  const results = useArticleSearch(query)

  function createTicket() {
    const subject = query.value.trim()
    navigateTo({ path: ROUTES.newTicket, query: subject ? { subject } : {} })
  }

  return { ...useSettingsModal(context), ...useKbHeader(context), query, results, createTicket }
}
