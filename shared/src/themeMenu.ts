import { computed, h } from "vue";
import { useColorScheme, type ColorScheme } from "frappe-ui";
import { __ } from "./translation";

export function useThemeMenuItem() {
  const { colorScheme, setColorScheme } = useColorScheme();

  const option = (value: ColorScheme, label: string, icon: string) => ({
    label,
    icon,
    slots: {
      suffix: () =>
        colorScheme.value === value
          ? h("span", { class: "lucide-check size-4 text-ink-gray-6" })
          : null,
    },
    onClick: () => setColorScheme(value),
  });

  return computed(() => ({
    icon: "lucide-moon",
    label: __("Toggle theme"),
    submenu: [
      option("light", __("Light Mode"), "lucide-sun"),
      option("dark", __("Dark Mode"), "lucide-moon"),
      option("system", __("System Default"), "lucide-monitor"),
    ],
  }));
}
