// Fixed colours, not theme tokens: a banner is brand art and looks the same in dark mode.
// Photos are hotlinked from Unsplash, as their guidelines ask.
const unsplash = (id: string) =>
  `center / cover url("https://images.unsplash.com/photo-${id}?w=2400&h=400&fit=crop&auto=format&q=80")`;

export const BANNER_PRESETS = [
  {
    name: "Dots",
    dark: false,
    background:
      "radial-gradient(#d4d4d4 1px, transparent 1.5px) 0 0 / 20px 20px, #fafafa",
  },
  {
    name: "Slate",
    dark: true,
    background: "linear-gradient(135deg, #272b33, #4a4f59)",
  },
  {
    name: "Sage",
    dark: false,
    background: "linear-gradient(135deg, #e4ebe1, #bccfb6)",
  },
  {
    name: "Paper",
    dark: false,
    background: unsplash("1603513492128-ba7bc9b3e143"),
  },
  {
    name: "Haze",
    dark: false,
    background: unsplash("1508614999368-9260051292e5"),
  },
  {
    name: "Sky",
    dark: true,
    background: unsplash("1640888760062-731cf8fa1412"),
  },
] as const;

export function findBannerPreset(name?: string | null) {
  return BANNER_PRESETS.find((preset) => preset.name === name);
}
