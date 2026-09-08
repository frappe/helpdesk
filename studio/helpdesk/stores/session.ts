import { computed, ref } from 'vue'
import { ROUTES } from '@app/routes'
import { call } from 'frappe-ui'

// Who is looking at the portal, and what it may offer them. The published Studio app
// is rendered from a bare template with no boot payload, so login state has to be
// asked for — `helpdesk.api.config.get_config` is the one endpoint the helpdesk
// already exposes to guests, and it carries the ticket setting too.

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

  // Guest until told otherwise: the topbar renders before the call returns, and
  // showing "Log in" to a signed-in user for a moment beats the reverse.
  const isGuest = computed(() => (config.value?.session_user || 'Guest') === 'Guest')

  /** Raising a ticket needs an account to put it on. */
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

  // A guest has no tickets, account or session to offer, so the menu keeps only what
  // works signed out.
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

  // A private knowledge base answers a signed-out reader with a permission error on
  // every call, so send them to sign in rather than render a shell that cannot fill.
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

  // Posted rather than navigated to: frappe only accepts POST on logout, so following
  // the link landed on a 403 page without ending the session. Back to the portal
  // home afterwards — signing out should leave you at its door, as a visitor.
  async function signOut() {
    try {
      await call('logout')
    } catch (error) {
      console.error(error)
    }
    window.location.href = ROUTES.appRoot
  }

  /** `isFeedbackMandatory` is read straight off it, so the payload itself is exported. */
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
