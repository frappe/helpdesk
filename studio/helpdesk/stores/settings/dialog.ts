import { watch } from 'vue'

// Opening, closing and the URL hash that drives both. The dialog lives in the hash
// (#settings/<tab>[/<organization>[/invite]]) so it layers over the page underneath
// and survives a refresh; the topbar menu opens it by pushing that hash. Every screen
// the dialog can show gets its own segment, which is what makes the device back
// button step back through them one at a time instead of dismissing the whole dialog.

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

  // Bound once per app, through `afterEach` rather than a watcher on the route,
  // because a page script's `route` is a snapshot taken when the script ran.
  let routerBound = false
  // Held here rather than captured in the watch: every page hands over its own router
  // proxy, and the one the first page gave is tied to a component that has since gone —
  // writing the hash through it did nothing, so the URL stopped following the dialog.
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

  // The router reaches a page script through a reactive proxy, which unwraps refs — so
  // `currentRoute` is the route itself there, and the ref only outside that proxy.
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

  // Organization names carry spaces, which the router escapes on the way into the URL
  // and hands back escaped after a popstate — so every hash is read decoded, and the
  // ones we build stay unescaped and let the router do that job once.
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
    // Leaving a screen the way we came in unwinds history rather than growing it —
    // pushing the parent again would leave the device back button pointing forward,
    // into the very screen just closed.
    const previous = previousHash()
    if (previous !== null && readHash(previous) === hash) return router.back()
    // The path travels with it: a bare `{ hash }` resolves against whatever the router
    // thinks is current, which is not always the page the dialog is layered over.
    router.push({ path: current.path, query: current.query, hash })
  }

  // vue-router keeps the entry behind this one in history state, as a full path —
  // query and all — so only the part before the query names the page.
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
