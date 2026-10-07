// Theme tokens, so a banner follows the reader's light or dark mode. Thinned with the page
// background: the raw dark-mode tints read as saturated blocks.
const tint = (color: string) =>
  `color-mix(in oklab, var(--surface-${color}-3) 40%, var(--surface-base))`;

// Pattern spacing follows --banner-pattern-scale, so a small swatch still shows a few repeats.
const cell = (size: number) =>
  `calc(${size}px * var(--banner-pattern-scale, 1))`;

// keep in sync with HD Settings banner_preset options and BannerPicker.vue labels
export const BANNER_PRESETS = [
  { name: "Gray", background: tint("gray") },
  { name: "Blue", background: tint("blue") },
  { name: "Violet", background: tint("violet") },
  {
    name: "Lines",
    background: `repeating-linear-gradient(135deg, var(--outline-gray-2) 0 1px, transparent 1px ${cell(
      10
    )}), ${tint("gray")}`,
  },
] as const;

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}
