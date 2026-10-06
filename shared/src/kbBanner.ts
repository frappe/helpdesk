// Theme tokens, so a banner follows the reader's light or dark mode. Thinned with the page
// background: the raw dark-mode tints read as saturated blocks.
const tint = (color: string) =>
  `color-mix(in oklab, var(--surface-${color}-3) 40%, var(--surface-base))`;

// keep in sync with HD Settings banner_preset options and BannerPicker.vue labels
export const BANNER_PRESETS = [
  { name: "Gray", background: tint("gray") },
  { name: "Blue", background: tint("blue") },
  { name: "Green", background: tint("green") },
  { name: "Amber", background: tint("amber") },
  { name: "Violet", background: tint("violet") },
] as const;

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}
