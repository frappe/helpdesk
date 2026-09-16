import { watch } from 'vue'

// The dialog lives in the hash (#settings/<tab>[/<organization>[/invite]]), a segment per
// screen, so the device back button steps through them instead of dismissing the dialog.

const HASH_ROOT = 'settings'

export function createSettingsDialog(core, organization) {
  function openSettings(tab) {
    core.settingsTab.value = tab || 'profile'
    core.settingsOpen.value = true
    organization.inviteOpen.value = false
    organization.closeOrganization()
    core.loadSettings()
  }

  function closeSettings() {
    core.settingsOpen.value = false
  }

  // `afterEach`, not a route watcher: a page script's `route` is a snapshot.
  let routerBound = false
  // Held, not captured: each page hands over its own proxy and the first page's is dead.
  let router = null

  function bindRouter(value) {
    if (!value) return
    router = value
    if (routerBound) return
    routerBound = true
    applyHash(currentRoute().hash)
    router.afterEach((to) => applyHash(to.hash))
    watch(
      [core.settingsOpen, core.settingsTab, organization.selectedOrg, organization.inviteOpen],
      () => pushHash(),
    )
  }

  // A page script's router proxy unwraps refs, so `currentRoute` is the route itself there.
  function currentRoute() {
    return router?.currentRoute?.value || router?.currentRoute || {}
  }

  function applyHash(hash) {
    const [root, tab, ...rest] = readHash(hash).replace(/^#/, '').split('/')
    if (root !== HASH_ROOT) return closeSettings()
    if (core.settingsOpen.value) core.settingsTab.value = tab || 'profile'
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
    if (!core.settingsOpen.value) return ''
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
    if (!router) return
    const hash = settingsHash()
    const current = currentRoute()
    if (readHash(current.hash) === hash) return
    // Unwind history rather than grow it, or back points forward into the closed screen.
    const previous = previousHash()
    if (previous !== null && readHash(previous) === hash) return router.back()
    // The path travels with it: a bare `{ hash }` resolves against whatever is current.
    router.push({ path: current.path, query: current.query, hash })
  }

  // History state holds a full path, so only the part before the query names the page.
  function previousHash() {
    const previous = router?.options?.history?.state?.back
    if (typeof previous !== 'string') return null
    const index = previous.indexOf('#')
    const [location, hash] = index === -1 ? [previous, ''] : [previous.slice(0, index), previous.slice(index)]
    return location.split('?')[0] === currentRoute().path ? hash : null
  }

  return {
    openSettings,
    closeSettings,
    bindRouter,
  }
}
