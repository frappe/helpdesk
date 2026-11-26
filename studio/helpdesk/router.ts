// The settings dialog opens over any page at `<page>/settings/<screen>`.
export function settingsPath(pagePath: string, screens: string[]) {
  return [pagePath.replace(/\/$/, ''), 'settings', ...screens.map(encodeURIComponent)].join('/')
}

export default {
  extendRoute(route) {
    route.alias = `${route.path.replace(/\/$/, '')}/settings/:settings*`
  },
  setup(router) {
    // Links from when the dialog opened on `#settings/<screen>`.
    router.beforeEach((to) => {
      if (!to.hash.startsWith('#settings/')) return
      const screens = to.hash.slice('#settings/'.length).split('/')
      return { path: settingsPath(to.path, screens), query: to.query, replace: true }
    })
  },
}
