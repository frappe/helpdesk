// Mixed with the page background: raw dark-mode tints look saturated.
const tint = (color: string) =>
  `color-mix(in oklab, var(--surface-${color}-3) 40%, var(--surface-base))`;

// Scaled so small swatches still show a few repeats.
const cell = (size: number) =>
  `calc(${size}px * var(--banner-pattern-scale, 1))`;

// keep in sync with HD Settings banner_preset options and BannerPicker.vue labels
export const BANNER_PRESETS = [
  {
    name: "Lines",
    background: `repeating-linear-gradient(135deg, var(--outline-gray-2) 0 1px, transparent 1px ${cell(
      10
    )}), ${tint("gray")}`,
  },
  { name: "Gray", background: tint("gray") },
  { name: "Blue", background: tint("blue") },
  { name: "Violet", background: tint("violet") },
] as const;

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}
