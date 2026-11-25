import { __ } from "./translation";

const layers = (...gradients: string[]) => gradients.join(", ");

// keep in sync with HD Settings banner_preset options and BannerPicker.vue labels
export const BANNER_PRESETS = [
  {
    name: "Soft Grain",
    background:
      "radial-gradient(rgba(23, 43, 77, 0.05) 0.5px, transparent 0.7px) 0 0 / 4px 4px #f1f3f6",
  },
  {
    name: "Aurora Mist",
    background: layers(
      "radial-gradient(100% 120% at 0% 50%, #cfe3f6 0%, transparent 55%)",
      "radial-gradient(90% 120% at 100% 45%, #c7eef0 0%, transparent 55%)",
      "radial-gradient(60% 80% at 100% 70%, #e7f2cf 0%, transparent 60%)",
      "linear-gradient(90deg, #e7eef5, #eef5f4) #eef4f4"
    ),
  },
  {
    name: "Aurora Mint",
    background: layers(
      "radial-gradient(100% 120% at 0% 50%, #cdeef0 0%, transparent 55%)",
      "radial-gradient(90% 120% at 100% 50%, #d6f0dd 0%, transparent 55%)",
      "linear-gradient(120deg, #eef8f6, #f1faf2) #eef8f4"
    ),
  },
  {
    name: "Aurora Dusk",
    background: layers(
      "radial-gradient(100% 120% at 0% 40%, #c3d6f5 0%, transparent 55%)",
      "radial-gradient(90% 120% at 100% 55%, #d2cdf2 0%, transparent 55%)",
      "radial-gradient(70% 90% at 80% 90%, #c9d9f3 0%, transparent 60%)",
      "linear-gradient(90deg, #e6ebf8, #eceaf7) #e9ecf8"
    ),
  },
  {
    name: "Mesh Blue",
    background: layers(
      "radial-gradient(60% 80% at 20% 25%, #d7e9fb 0%, transparent 60%)",
      "radial-gradient(55% 75% at 80% 20%, #d9f0f2 0%, transparent 60%)",
      "radial-gradient(70% 80% at 65% 90%, #e6e0f6 0%, transparent 60%)",
      "radial-gradient(60% 70% at 15% 85%, #dcecf8 0%, transparent 60%) #eef4fb"
    ),
  },
] as const;

const COLOR = /#[0-9a-f]{6}\b|rgba?\([^)]*\)/gi;

const darken = (color: string) =>
  `hsl(from ${color} h min(calc(s * 0.92), 55) clamp(4, calc(6 + (100 - l) * 0.9), 92) / alpha)`;

export function bannerPresetBackground(name: string | null | undefined, dark: boolean) {
  const background = findBannerPreset(name)?.background || "";
  return dark ? background.replace(COLOR, darken) : background;
}

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}

export const defaultBannerTitle = () => __("Here's what might help");
export const defaultBannerSubtitle = (brandName?: string) =>
  brandName
    ? __("Explore answers to frequently asked questions about {0}.", [brandName])
    : __("Explore answers to frequently asked questions.");
