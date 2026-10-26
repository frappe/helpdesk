import { computed, ref } from 'vue'
import { useMediaQuery } from '@vueuse/core'
import { call, setConfig } from 'frappe-ui'
import { spritePlugin } from 'frappe-ui/experimental'
import { ROUTES } from '@helpdesk/shared/portalRoutes'
import { __ } from '@helpdesk/shared/translation'
import { setLocalTimezone } from '@helpdesk/shared/timezone'

// From boot: must be set before the first date renders.
setConfig('systemTimezone', window.boot?.system_timezone)
// The zone picked in Settings, else the system's.
setLocalTimezone(window.boot?.user_timezone)

// Stored icons can be any lucide name, beyond Studio's build-time classes.
if (!document.getElementById('lucide-sprite')) spritePlugin.install()

if (window.boot?.send_guest_to_login) {
  document.documentElement.style.visibility = 'hidden'
  location.replace(loginUrl())
} else if (location.pathname === '/' && window.boot?.home_page && window.boot.home_page !== '/') {
  // Else the router reads `/` as the portal root, the knowledge base.
  location.replace(window.boot.home_page)
}

const store = createSessionStore()

export function useSession() {
  store.loadSession()
  return store
}

function createSessionStore() {
  const config = ref(null)
  let sessionRequest = null

  const isGuest = computed(() => (config.value?.session_user || 'Guest') === 'Guest')
  const canCreateTicket = computed(() => !isGuest.value)
  const canGiveFeedback = computed(() => !isGuest.value || Boolean(config.value?.allow_anonymous_article_voting))
  const isPublicKnowledgeBase = computed(() => Boolean(config.value?.public_knowledge_base))
  const isAgent = computed(() => Boolean(config.value?.is_agent))
  const canEditSettings = computed(() => Boolean(config.value?.can_edit_settings))
  const brandLogo = computed(() => config.value?.brand_logo || config.value?.favicon || '')
  const brandName = computed(() => config.value?.brand_name || window.boot?.brand_name || 'Helpdesk')
  // frappe writes `dd-mm-yyyy`; dayjs wants uppercase tokens.
  const dateFormat = computed(() => config.value?.date_format?.toUpperCase())
  // Tailwind `sm`, the desk's mobile cut-off.
  const isPhone = useMediaQuery('(max-width: 639px)')
  // The header has no room for the full label on a phone.
  const raiseTicketLabel = computed(() => (isPhone.value ? __('Create') : __('Raise a ticket')))

  function loadSession() {
    if (sessionRequest) return sessionRequest
    sessionRequest = call('helpdesk.api.config.get_config')
      .then((data) => (config.value = data))
      .then(sendGuestToLogin)
      .catch((error) => {
        sessionRequest = null
        console.error(error)
      })
    return sessionRequest
  }

  function reloadSession() {
    sessionRequest = null
    return loadSession()
  }

  // Once per app: every page passes the same socket.
  let listeningForSettings = false
  function reloadOnSettingsUpdate(socket) {
    if (listeningForSettings || !socket) return
    listeningForSettings = true
    socket.on('helpdesk:settings-updated', reloadSession)
  }

  // A private knowledge base 403s every guest call.
  function sendGuestToLogin() {
    if (!isGuest.value || isPublicKnowledgeBase.value) return
    signIn()
  }

  function signIn() {
    window.location.href = loginUrl()
  }

  // frappe only accepts POST on logout.
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
    reloadOnSettingsUpdate,
    isGuest,
    isPublicKnowledgeBase,
    canCreateTicket,
    canGiveFeedback,
    isAgent,
    canEditSettings,
    brandLogo,
    brandName,
    dateFormat,
    isPhone,
    raiseTicketLabel,
    signIn,
    loadSession,
    reloadSession,
    signOut,
  }
}

function loginUrl() {
  return `/login?redirect-to=${encodeURIComponent(location.pathname + location.search)}`
}
