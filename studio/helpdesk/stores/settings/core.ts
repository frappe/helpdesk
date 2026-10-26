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
import { settingsPath } from '@app/router'

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
    () => pushPath(),
  )

  // `afterEach`: a page script's `route` is a snapshot.
  let isWatchingRoute = false

  function watchRoute() {
    if (isWatchingRoute) return
    isWatchingRoute = true
    applyRoute(currentRoute())
    afterEachRoute(applyRoute)
  }

  async function applyRoute(route) {
    const screens = readScreens(route)
    if (!screens) return closeSettings()
    // Guests have no account; unseen tabs would open blank.
    await session.loadSession()
    if (session.isGuest.value) {
      closeSettings()
      return navigateTo({ path: pagePath(route), query: route.query, hash: route.hash, replace: true })
    }
    const [routeTab, ...rest] = screens
    const allowed = TABS.includes(routeTab) && (!EDITOR_TABS.includes(routeTab) || session.canEditSettings.value)
    const tab = allowed ? routeTab : 'profile'
    if (core.isSettingsOpen.value) core.settingsTab.value = tab
    else openSettings(tab)
    const invite = rest[rest.length - 1] === 'invite'
    if (invite) rest.pop()
    applyOrganization(rest.join('/'), invite)
  }

  function applyOrganization(org, invite) {
    if (!org) return organization.closeOrganization()
    if (org !== organization.selectedOrganization.value) organization.openOrganization(org)
    organization.inviteOpen.value = invite
  }

  // One path segment per screen, so device back steps through the dialog.
  function targetPath(route) {
    const page = pagePath(route)
    if (!core.isSettingsOpen.value) return page
    const screens = [core.settingsTab.value]
    if (organization.selectedOrganization.value) screens.push(organization.selectedOrganization.value)
    if (organization.selectedOrganization.value && organization.inviteOpen.value) screens.push('invite')
    return settingsPath(page, screens)
  }

  // The `<page>/settings/:settings*` alias from router.ts; null off it.
  function readScreens(route) {
    const screens = route.params?.settings
    if (screens === undefined) return null
    return Array.isArray(screens) ? screens : [screens].filter(Boolean)
  }

  function pagePath(route) {
    const screens = readScreens(route)
    if (!screens) return route.path
    return route.path.replace(/\/$/, '').split('/').slice(0, -(screens.length + 1)).join('/') || '/'
  }

  // Paths come from the router, the address bar and here, each escaped its own way.
  function decode(path) {
    try {
      return decodeURIComponent(String(path || ''))
    } catch {
      return String(path || '')
    }
  }

  function pushPath() {
    const current = currentRoute()
    if (!current.path) return
    const path = targetPath(current)
    if (decode(current.path) === decode(path)) return
    // Unwind history, or back points into the closed screen.
    const previous = previousLocation()
    if (previous !== null && decode(previous.split(/[?#]/)[0]) === decode(path)) return navigateBack()
    navigateTo({ path, query: current.query, hash: current.hash })
  }

  return {
    openSettings,
    watchRoute,
  }
}
