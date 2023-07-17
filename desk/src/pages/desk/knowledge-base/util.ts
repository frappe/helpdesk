import { h } from "vue";
import { Icon } from "@iconify/vue";

export function getIcon(icon: string) {
  const i = icon || "box";
  const l = `lucide:${i}`;
  return h(Icon, { icon: l });
}
