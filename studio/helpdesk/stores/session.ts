import { computed, ref } from 'vue'
import { call } from 'frappe-ui'
import { ROUTES } from '@app/routes'

// A published Studio app renders from a bare template with no boot payload, so login
// state has to be asked for; `get_config` is the one endpoint guests may call.

const store = createSessionStore()

export function useSession() {
  store.loadSession()
  return store
}

function createSessionStore() {
  const config = ref(null)
  let sessionRequest = null

  // Guest until told otherwise: the topbar renders before the call returns.
  const isGuest = computed(() => (config.value?.session_user || 'Guest') === 'Guest')
  const canCreateTicket = computed(() => !isGuest.value)
  const isPublicKnowledgeBase = computed(() => Boolean(config.value?.public_knowledge_base))
  // Only agents have the desk to return to; for anyone else the link is a 403.
  const isAgent = computed(() => Boolean(config.value?.is_agent))
  // The favicon is the helpdesk's fallback everywhere else, so the topbar falls back with it.
  const brandLogo = computed(() => config.value?.brand_logo || config.value?.favicon || '')

  // Back to the page they were reading, not to the agent desk.
  const loginUrl = computed(
    () => `/login?redirect-to=${encodeURIComponent(window.location.pathname + window.location.search)}`,
  )

  function loadSession() {
    if (sessionRequest) return sessionRequest
    sessionRequest = call('helpdesk.api.config.get_config')
      .then((data) => (config.value = data))
      .then(sendGuestToLogin)
      .catch((error) => console.error(error))
    return sessionRequest
  }

  // A private knowledge base 403s every call, so sign in beats an unfillable shell.
  function sendGuestToLogin() {
    if (!isGuest.value || isPublicKnowledgeBase.value) return
    signIn()
  }

  function signIn() {
    window.location.href = loginUrl.value
  }

  // Posted, not navigated: frappe only accepts POST on logout.
  async function signOut() {
    try {
      await call('logout')
    } catch (error) {
      console.error(error)
    }
    window.location.href = ROUTES.appRoot
  }

  return {
    config,
    isGuest,
    canCreateTicket,
    isPublicKnowledgeBase,
    isAgent,
    brandLogo,
    loginUrl,
    loadSession,
    signIn,
    signOut,
  }
}
