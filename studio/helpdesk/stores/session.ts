import { computed, ref } from 'vue'
import { ROUTES } from '@app/routes'
import { call } from 'frappe-ui'

// A published Studio app renders from a bare template with no boot payload, so login
// state has to be asked for; `get_config` is the one endpoint guests may call.

const store = createSessionStore()

export function useSession(context) {
  if (context?.router) store.bindRouter(context.router)
  store.loadSession()
  return store
}

function createSessionStore() {
  const config = ref(null)
  let router = null
  let loading = null

  // Guest until told otherwise: the topbar renders before the call returns.
  const isGuest = computed(() => (config.value?.session_user || 'Guest') === 'Guest')

  const canCreateTicket = computed(() => !isGuest.value)

  const isPublicKnowledgeBase = computed(
    () => Boolean(config.value?.public_knowledge_base)
  )

  // Back to the page they were reading, not to the agent desk.
  const loginUrl = computed(
    () =>
      `/login?redirect-to=${encodeURIComponent(
        window.location.pathname + window.location.search
      )}`
  )

  // A guest has no tickets, account or session to offer.
  const accountMenuOptions = computed(() =>
    isGuest.value
      ? [{ icon: 'lucide-log-in', label: 'Log in', onClick: signIn }]
      : [
          { icon: 'lucide-inbox', label: 'My tickets', onClick: () => go(ROUTES.ticketList) },
          { icon: 'lucide-user', label: 'My account', onClick: openSettings },
          { icon: 'lucide-log-out', label: 'Log out', onClick: signOut },
        ]
  )

  function loadSession() {
    if (loading) return loading
    loading = call('helpdesk.api.config.get_config')
      .then((data) => (config.value = data))
      .then(sendGuestToLogin)
      .catch((error) => console.error(error))
    return loading
  }

  // A private knowledge base 403s every call, so sign in beats an unfillable shell.
  function sendGuestToLogin() {
    if (!isGuest.value || isPublicKnowledgeBase.value) return
    signIn()
  }

  function bindRouter(value) {
    router = router || value
  }

  function go(path) {
    router?.push(path)
  }

  function openSettings() {
    router?.push({ hash: '#settings/profile' })
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

  // `isFeedbackMandatory` is read straight off it, so the payload itself is exported.
  return {
    config,
    isGuest,
    canCreateTicket,
    isPublicKnowledgeBase,
    loginUrl,
    accountMenuOptions,
    loadSession,
    bindRouter,
  }
}
