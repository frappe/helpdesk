// Fixed colours, not theme tokens: a banner looks the same in dark mode.
// keep in sync with HD Settings banner_preset options and BannerPicker.vue labels
export const BANNER_PRESETS = [
  { name: "Stone", dark: false, background: "#f1efea" },
  { name: "Blue", dark: false, background: "#e9f0f8" },
  { name: "Green", dark: false, background: "#e8f1ec" },
  { name: "Charcoal", dark: true, background: "#2a2c30" },
  { name: "Navy", dark: true, background: "#1c2b45" },
  { name: "Forest", dark: true, background: "#1e3a30" },
] as const;

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}
