import { ref, computed, watch } from 'vue'
import { FileUploadHandler, call, toast } from 'frappe-ui'
import { __ } from '@helpdesk/shared/translation'
import {
  afterEachRoute,
  currentRoute,
  navigateBack,
  navigateTo,
  previousLocation,
} from '@app/stores/router'
import { errorMessage } from '@app/utils'

export function createSettingsCore() {
  const isSettingsOpen = ref(false)
  const settingsTab = ref<'profile' | 'members' | 'knowledge-base' | 'portal-permissions'>('profile')
  const account = ref(null)
  const isSettingsBusy = ref(false)

  const settingsUser = computed(() => account.value?.user || {})
  const organizations = computed(() => account.value?.organizations || [])

  const reloadHooks = []
  function afterLoad(hook) {
    reloadHooks.push(hook)
  }

  async function loadSettings() {
    try {
      account.value = await call('helpdesk.api.organization.get_account')
      for (const hook of reloadHooks) await hook()
    } catch (error) {
      console.error(error)
      toast.error(__('Could not load settings'))
    }
  }

  // `landed` reports a change that saved but whose mail failed.
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
      const file = input.files?.[0]
      if (!file) return
      const uploaded = await new FileUploadHandler()
        .upload(file, { private: false, optimize: true })
        .catch(() => toast.error(__('Could not upload the image')))
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
    afterLoad,
    loadSettings,
    run,
    pickImage,
  }
}

// One hash segment per screen, so the device back button steps through the dialog.
const HASH_ROOT = 'settings'

export function createSettingsDialog(core, organization) {
  function openSettings(tab) {
    core.settingsTab.value = tab || 'profile'
    core.isSettingsOpen.value = true
    organization.closeOrganization()
    core.loadSettings()
  }

  function closeSettings() {
    core.isSettingsOpen.value = false
  }

  // At module load, not in watchRoute: Studio stops the page's effect scope on navigation.
  watch(
    [core.isSettingsOpen, core.settingsTab, organization.selectedOrganization, organization.inviteOpen],
    () => pushHash(),
  )

  // `afterEach`, not a route watcher: a page script's `route` is a snapshot.
  let isWatchingRoute = false

  function watchRoute() {
    if (isWatchingRoute) return
    isWatchingRoute = true
    applyHash(currentRoute().hash)
    afterEachRoute((to) => applyHash(to.hash))
  }

  function applyHash(hash) {
    const [root, tab, ...rest] = readHash(hash).replace(/^#/, '').split('/')
    if (root !== HASH_ROOT) return closeSettings()
    if (core.isSettingsOpen.value) core.settingsTab.value = tab || 'profile'
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

  // Names carry spaces, which the router escapes, so every hash is read decoded.
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
