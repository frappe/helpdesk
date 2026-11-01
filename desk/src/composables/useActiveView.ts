import type { Ref } from "vue";
import { computed, effectScope } from "vue";
import {
  isNavigationFailure,
  NavigationFailureType,
  useRoute,
  useRouter,
  type RouteLocationNormalizedLoaded,
  type Router,
} from "vue-router";
import { userStorage } from "./userStorage";

const storedViews = new Map<string, Ref<string | null>>();

/** The saved view open on a list route, kept out of the URL. Tabs do not sync,
 * so switching views in one tab leaves the others alone until they reload. */
function viewRef(listRoute: string) {
  let view = storedViews.get(listRoute);
  if (!view) {
    // Detached, or the write-back watcher stops with the first caller's component.
    view = effectScope(true).run(() =>
      userStorage<string | null>(`active_view:${listRoute}`, null, {
        listenToStorageChanges: false,
        writeDefaults: false,
      })
    )!;
    storedViews.set(listRoute, view);
  }
  return view;
}

/** Empty when the list route shows its default list. */
export function getActiveView(listRoute: string): string {
  return viewRef(listRoute).value || "";
}

/** Omit `view` to go back to the default list. */
export function setActiveView(listRoute: string, view?: string) {
  viewRef(listRoute).value = view || null;
}

/** The list whose view a page follows; a ticket page follows the ticket list. */
export function listRouteOf(route: RouteLocationNormalizedLoaded): string {
  return route.meta.list ?? (route.name as string);
}

/** Opens `view` on a list route, or its default list when `view` is omitted.
 * The view is set once the route lands, so the list reloads once, not twice. */
export function openViewWith(router: Router, listRoute: string, view?: string) {
  const { name, query } = router.currentRoute.value;
  if (name === listRoute && !Object.keys(query).length) {
    setActiveView(listRoute, view);
    return;
  }
  const stop = router.afterEach((to, _from, failure) => {
    // A newer push cancelled this one; wait for it to land. Listeners run in
    // the order they were added, so the latest pick is set last and wins.
    if (isNavigationFailure(failure, NavigationFailureType.cancelled)) return;
    stop();
    if (!failure && to.name === listRoute) setActiveView(listRoute, view);
  });
  router.push({ name: listRoute });
}

/** Active view of the current page's list, plus `openView`: `openViewWith`
 * bound to this component's router. */
export function useActiveView() {
  const route = useRoute();
  const router = useRouter();
  return {
    activeViewName: computed(() => getActiveView(listRouteOf(route))),
    openView: (listRoute: string, view?: string) =>
      openViewWith(router, listRoute, view),
  };
}
