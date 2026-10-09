import { computed, ref } from 'vue'
import { call, setConfig } from 'frappe-ui'
import { ROUTES } from '@app/routes'

// From boot, not `get_config`: it must be set before the first date renders.
setConfig('systemTimezone', window.boot?.system_timezone)

// `get_config` is the one call guests may make.

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
  const isAgent = computed(() => Boolean(config.value?.is_agent))
  const canEditSettings = computed(() => Boolean(config.value?.can_edit_settings))
  const brandLogo = computed(() => config.value?.brand_logo || config.value?.favicon || '')
  const brandName = computed(() => config.value?.brand_name || 'Helpdesk')

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
    window.location.href = `/login?redirect-to=${encodeURIComponent(location.pathname + location.search)}`
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
    isAgent,
    canEditSettings,
    brandLogo,
    brandName,
    loadSession,
    signIn,
    signOut,
  }
}
