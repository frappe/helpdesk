import { ref, watch } from 'vue'
import { createResource, debounce } from 'frappe-ui'
import { ROUTES } from '@app/routes'
import { navigateTo } from '@app/stores/router'
import { useSettingsModal } from '@app/stores/settings'

const SEARCH_DEBOUNCE_MS = 300
const MIN_QUERY = 3

// Search first, and only offer a ticket once the knowledge base comes up empty.
export default function setup(context) {
  const { route } = context

  // Seeded from the header search box, so the results are already on screen.
  const query = ref(String(route.query.q || ''))

  const results = createResource({
    url: 'helpdesk.api.knowledge_base.search_articles',
    method: 'GET',
    makeParams: () => ({ query: query.value }),
  })

  // Below three characters a query matches too much to be worth showing.
  const search = debounce(() => {
    if (query.value.trim().length >= MIN_QUERY) results.fetch()
  }, SEARCH_DEBOUNCE_MS)
  watch(query, search, { immediate: true })

  // The query travels along as the subject, so nothing is typed twice.
  function createTicket() {
    const subject = query.value.trim()
    navigateTo({ path: ROUTES.newTicket, query: subject ? { subject } : {} })
  }

  return { ...useSettingsModal(context), query, results, createTicket }
}
