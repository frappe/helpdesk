import { h } from "vue";
import { Icon } from "@iconify/vue";

/**
 * Return an `Icon` component or icon name as string
 */
export function getIcon(icon?: string, asStr?: boolean) {
  const i = icon || "box";
  const l = `lucide:${i}`;
  if (asStr) return l;
  return h(Icon, { icon: l });
}
