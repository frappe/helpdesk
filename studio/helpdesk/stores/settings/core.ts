import { ref, computed, watch } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import {
  afterEachRoute,
  currentRoute,
  navigateBack,
  navigateTo,
  previousLocation,
} from '@app/stores/router'
import { getErrorMessage } from '@helpdesk/shared/utils'

export function createSettingsCore() {
  const isSettingsOpen = ref(false)
  const settingsTab = ref<'profile' | 'members' | 'knowledge-base' | 'portal-settings'>('profile')
  const account = ref(null)
  const isSettingsBusy = ref(false)

  const settingsUser = computed(() => account.value?.user || {})
  const organizations = computed(() => account.value?.organizations || [])
  // Set even on failure, so nothing waits forever.
  const settingsLoaded = ref(false)

  const reloadHooks = []
  function afterLoad(hook) {
    reloadHooks.push(hook)
  }

  async function loadSettings() {
    try {
      account.value = await call('helpdesk.api.customer.get_portal_account')
      for (const hook of reloadHooks) await hook()
    } catch (error) {
      console.error(error)
      toast.error(__('Could not load settings'))
    } finally {
      settingsLoaded.value = true
    }
  }

  // Pages need the account once; opening the dialog refetches it.
  let firstLoad: Promise<void> | null = null
  function ensureSettings() {
    return (firstLoad ??= loadSettings())
  }

  // `landed`: saved but the mail failed. `reload`: refetch what changed.
  async function run(action, successMessage, landed?, reload = loadSettings) {
    if (isSettingsBusy.value) return
    isSettingsBusy.value = true
    try {
      await action()
      if (successMessage) toast.success(successMessage)
      await reload()
    } catch (error) {
      console.error(error)
      await reload()
      const partial = landed?.()
      if (partial) toast.warning(partial)
      else getErrorMessage(error, true, __('Something went wrong'))
    } finally {
      isSettingsBusy.value = false
    }
  }

  return {
    isSettingsOpen,
    settingsTab,
    isSettingsBusy,
    settingsUser,
    organizations,
    settingsLoaded,
    afterLoad,
    loadSettings,
    ensureSettings,
    run,
  }
}

// One hash segment per screen, so device back steps through the dialog.
const HASH_ROOT = 'settings'

// Only settings editors get these.
const EDITOR_TABS = ['knowledge-base', 'portal-settings']
const TABS = ['profile', 'members', ...EDITOR_TABS]

export function createSettingsDialog(core, organization, session) {
  function openSettings(tab) {
    core.settingsTab.value = tab || 'profile'
    core.isSettingsOpen.value = true
    organization.closeOrganization()
    core.loadSettings()
  }

  function closeSettings() {
    core.isSettingsOpen.value = false
  }

  // Not in watchRoute: Studio stops the page's effect scope on navigation.
  watch(
    [core.isSettingsOpen, core.settingsTab, organization.selectedOrganization, organization.inviteOpen],
    () => pushHash(),
  )

  // `afterEach`: a page script's `route` is a snapshot.
  let isWatchingRoute = false

  function watchRoute() {
    if (isWatchingRoute) return
    isWatchingRoute = true
    applyHash(currentRoute().hash)
    afterEachRoute((to) => applyHash(to.hash))
  }

  async function applyHash(hash) {
    const [root, hashTab, ...rest] = readHash(hash).replace(/^#/, '').split('/')
    if (root !== HASH_ROOT) return closeSettings()
    // Guests have no account; unseen tabs would open blank.
    await session.loadSession()
    if (session.isGuest.value) return closeSettings()
    const allowed = TABS.includes(hashTab) && (!EDITOR_TABS.includes(hashTab) || session.canEditSettings.value)
    const tab = allowed ? hashTab : 'profile'
    if (core.isSettingsOpen.value) core.settingsTab.value = tab
    else openSettings(tab)
    const invite = rest[rest.length - 1] === 'invite'
    if (invite) rest.pop()
    applyOrganizationHash(rest.join('/'), invite)
  }

  function applyOrganizationHash(org, invite) {
    if (!org) return organization.closeOrganization()
    if (org !== organization.selectedOrganization.value) organization.openOrganization(org)
    organization.inviteOpen.value = invite
  }

  function settingsHash() {
    if (!core.isSettingsOpen.value) return ''
    const parts = [HASH_ROOT, core.settingsTab.value]
    if (organization.selectedOrganization.value) parts.push(organization.selectedOrganization.value)
    if (organization.selectedOrganization.value && organization.inviteOpen.value) parts.push('invite')
    return `#${parts.join('/')}`
  }

  // The router escapes spaces in names.
  function readHash(hash) {
    try {
      return decodeURIComponent(String(hash || ''))
    } catch {
      return String(hash || '')
    }
  }

  function pushHash() {
    const hash = settingsHash()
    const current = currentRoute()
    if (readHash(current.hash) === hash) return
    // Unwind history, or back points into the closed screen.
    const previous = previousHash()
    if (previous !== null && readHash(previous) === hash) return navigateBack()
    // A bare `{ hash }` resolves against whatever route is current.
    navigateTo({ path: current.path, query: current.query, hash })
  }

  // History state holds a full path; compare only the page part.
  function previousHash() {
    const previous = previousLocation()
    if (previous === null) return null
    const index = previous.indexOf('#')
    const [location, hash] = index === -1 ? [previous, ''] : [previous.slice(0, index), previous.slice(index)]
    return location.split('?')[0] === currentRoute().path ? hash : null
  }

  return {
    openSettings,
    watchRoute,
  }
}
