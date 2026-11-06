// Spelt out so Tailwind's scanner sees every class.
const STATUS_DOT_CLASSES: Record<string, string> = {
  Black: "!text-ink-gray-9",
  Gray: "!text-gray-500",
  Blue: "!text-blue-500",
  Green: "!text-green-500",
  Red: "!text-red-500",
  Pink: "!text-pink-500",
  Orange: "!text-orange-500",
  Amber: "!text-amber-500",
  Yellow: "!text-yellow-500",
  Cyan: "!text-cyan-500",
  Teal: "!text-teal-500",
  Violet: "!text-violet-500",
  Purple: "!text-purple-500",
};

export function statusDotClass(color?: string | null): string {
  return STATUS_DOT_CLASSES[color ?? ""] ?? STATUS_DOT_CLASSES.Gray;
}
