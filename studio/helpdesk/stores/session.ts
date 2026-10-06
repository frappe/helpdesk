import { computed, ref } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { call } from 'frappe-ui'
import { ROUTES } from '@app/routes'

// A published Studio app has no boot payload; `get_config` is the one call guests may make.
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
  // Tailwind's `sm`, which the desk also takes as its mobile cut-off.
  const isPhone = useMediaQuery('(max-width: 639px)')

  function loadSession() {
    if (sessionRequest) return sessionRequest
    sessionRequest = call('helpdesk.api.config.get_config')
      .then((data) => (config.value = data))
      .then(sendGuestToLogin)
      .catch((error) => console.error(error))
    return sessionRequest
  }

  function reloadSession() {
    sessionRequest = null
    return loadSession()
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
    isPublicKnowledgeBase,
    canCreateTicket,
    isAgent,
    canEditSettings,
    brandLogo,
    brandName,
    isPhone,
    signIn,
    loadSession,
    reloadSession,
    signOut,
  }
}
