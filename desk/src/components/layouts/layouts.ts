import { type Component, defineAsyncComponent, shallowRef } from "vue";

type Kind = "desktop" | "mobile";

const loaders: Record<Kind, () => Promise<{ default: Component }>> = {
  desktop: () => import("./DesktopLayout.vue"),
  mobile: () => import("./MobileLayout.vue"),
};
const lazy: Record<Kind, Component> = {
  desktop: defineAsyncComponent(loaders.desktop),
  mobile: defineAsyncComponent(loaders.mobile),
};
const loaded = shallowRef<Partial<Record<Kind, Component>>>({});

/** The desk shell. A shell loaded ahead with `preloadLayout` draws at once. */
export function layoutFor(mobile: boolean): Component {
  const kind: Kind = mobile ? "mobile" : "desktop";
  return loaded.value[kind] ?? lazy[kind];
}

/** Loads the shell before the first page that needs it, such as the one setup hands over to. */
export async function preloadLayout(mobile: boolean) {
  const kind: Kind = mobile ? "mobile" : "desktop";
  const { default: layout } = await loaders[kind]();
  loaded.value = { ...loaded.value, [kind]: layout };
}
