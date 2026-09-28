import { ref, computed, watch } from 'vue'
import { call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import { usePreferences } from '@app/stores/preferences'
import {
  afterEachRoute,
  currentRoute,
  navigateBack,
  navigateTo,
  previousLocation,
} from '@app/stores/router'
import { errorMessage, uploadFiles } from '@app/utils'

export function createSettingsCore() {
  const isSettingsOpen = ref(false)
  const settingsTab = ref('profile') // 'profile' | 'members' | 'organization'
  const settingsData = ref(null)
  const isSettingsBusy = ref(false)

  const settingsUser = computed(() => settingsData.value?.user || {})
  const organizations = computed(() => settingsData.value?.organizations || [])

  const confirmAction = ref(null)
  // Apart from the options, so what is on the dialog survives its own closing animation.
  const isConfirmOpen = ref(false)

  function askConfirm(options) {
    confirmAction.value = options
    isConfirmOpen.value = true
  }

  function cancelConfirm() {
    isConfirmOpen.value = false
  }

  function acceptConfirm() {
    isConfirmOpen.value = false
    return confirmAction.value?.action?.()
  }

  // Modules that keep state derived from the payload re-seed themselves here.
  const reloadHooks = []
  function afterLoad(hook) {
    reloadHooks.push(hook)
  }

  async function loadSettings() {
    try {
      settingsData.value = await call('helpdesk.api.organization.get_settings')
      // By docname, not email: they differ for Administrator.
      usePreferences().loadPreferences(settingsUser.value.name)
      for (const hook of reloadHooks) await hook()
    } catch (error) {
      console.error(error)
      toast.error(__('Could not load settings'))
    }
  }

  // `landed` covers actions that mail synchronously, where a mail failure fails a
  // request whose change is already saved.
  async function run(action, successMessage, landed) {
    if (isSettingsBusy.value) return
    isSettingsBusy.value = true
    try {
      await action()
      if (successMessage) toast.success(successMessage)
      await loadSettings()
    } catch (error) {
      console.error(error)
      await loadSettings()
      const partial = landed?.()
      if (partial) toast.warning(partial)
      else toast.error(errorMessage(error, __('Something went wrong')))
    } finally {
      isSettingsBusy.value = false
    }
  }

  function pickImage(onUploaded) {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = 'image/*'
    input.onchange = async () => {
      const file = input.files && input.files[0]
      if (!file) return
      const [uploaded] = await uploadFiles([file], { private: false, optimize: true })
      if (uploaded) await onUploaded(uploaded.file_url)
    }
    input.click()
  }

  return {
    isSettingsOpen,
    settingsTab,
    isSettingsBusy,
    settingsUser,
    organizations,
    confirmAction,
    isConfirmOpen,
    askConfirm,
    cancelConfirm,
    acceptConfirm,
    afterLoad,
    loadSettings,
    run,
    pickImage,
  }
}

// The dialog lives in the hash (#settings/<tab>[/<organization>[/invite]]), a segment per
// screen, so the device back button steps through them instead of dismissing the dialog.

const HASH_ROOT = 'settings'

export function createSettingsDialog(core, organization) {
  function openSettings(tab) {
    core.settingsTab.value = tab || 'profile'
    core.isSettingsOpen.value = true
    organization.inviteOpen.value = false
    organization.closeOrganization()
    core.loadSettings()
  }

  function closeSettings() {
    core.isSettingsOpen.value = false
  }

  // `afterEach`, not a route watcher: a page script's `route` is a snapshot.
  let isWatchingRoute = false

  function watchRoute() {
    if (isWatchingRoute) return
    isWatchingRoute = true
    applyHash(currentRoute().hash)
    afterEachRoute((to) => applyHash(to.hash))
    watch(
      [core.isSettingsOpen, core.settingsTab, organization.selectedOrg, organization.inviteOpen],
      () => pushHash(),
    )
  }

  function applyHash(hash) {
    const [root, tab, ...rest] = readHash(hash).replace(/^#/, '').split('/')
    if (root !== HASH_ROOT) return closeSettings()
    if (core.isSettingsOpen.value) core.settingsTab.value = tab || 'profile'
    else openSettings(tab)
    const invite = rest[rest.length - 1] === 'invite'
    if (invite) rest.pop()
    // An organization is named by whatever is left, slashes and all.
    applyOrganizationHash(rest.join('/'), invite)
  }

  function applyOrganizationHash(org, invite) {
    if (!org) return organization.closeOrganization()
    if (org !== organization.selectedOrg.value) organization.openOrganization(org)
    organization.inviteOpen.value = invite
  }

  function settingsHash() {
    if (!core.isSettingsOpen.value) return ''
    const parts = [HASH_ROOT, core.settingsTab.value]
    if (organization.selectedOrg.value) parts.push(organization.selectedOrg.value)
    if (organization.selectedOrg.value && organization.inviteOpen.value) parts.push('invite')
    return `#${parts.join('/')}`
  }

  // Names carry spaces, which the router escapes, so every hash is read decoded.
  function readHash(hash) {
    try {
      return decodeURIComponent(String(hash || ''))
    } catch (error) {
      return String(hash || '')
    }
  }

  function pushHash() {
    const hash = settingsHash()
    const current = currentRoute()
    if (readHash(current.hash) === hash) return
    // Unwind history rather than grow it, or back points forward into the closed screen.
    const previous = previousHash()
    if (previous !== null && readHash(previous) === hash) return navigateBack()
    // The path travels with it: a bare `{ hash }` resolves against whatever is current.
    navigateTo({ path: current.path, query: current.query, hash })
  }

  // History state holds a full path, so only the part before the query names the page.
  function previousHash() {
    const previous = previousLocation()
    if (previous === null) return null
    const index = previous.indexOf('#')
    const [location, hash] = index === -1 ? [previous, ''] : [previous.slice(0, index), previous.slice(index)]
    return location.split('?')[0] === currentRoute().path ? hash : null
  }

  return {
    openSettings,
    closeSettings,
    watchRoute,
  }
}
