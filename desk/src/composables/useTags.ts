import { createListResource } from "frappe-ui";

export interface Tag {
  name: string;
  color?: string;
}

const DEFAULT_COLOR_CLASS = "bg-surface-gray-5";

// keys are stored on the Tag doc (Select field); values must be full literal
// Tailwind classes - the JIT scanner can't see `bg-surface-${name}`
export const TAG_COLORS: Record<string, string> = {
  Gray: DEFAULT_COLOR_CLASS,
  Black: "bg-surface-gray-10",
  Blue: "bg-surface-blue-6",
  Green: "bg-surface-green-6",
  Red: "bg-surface-red-6",
  Pink: "bg-surface-pink-6",
  Orange: "bg-surface-orange-6",
  Amber: "bg-surface-amber-6",
  Yellow: "bg-surface-yellow-6",
  Cyan: "bg-surface-cyan-6",
  Teal: "bg-surface-teal-6",
  Violet: "bg-surface-violet-6",
  Purple: "bg-surface-purple-6",
};
export const TAG_COLOR_NAMES = Object.keys(TAG_COLORS);

/** Dot class for a Tag's stored colour, falling back to Gray. */
export function colorToken(color?: string): string {
  return TAG_COLORS[color ?? ""] ?? DEFAULT_COLOR_CLASS;
}

let tagListResource: ReturnType<typeof createListResource<Tag>> | undefined;

/** Shared master list of helpdesk tags, fetched once. Per-document tag changes
 * go through `helpdesk.api.tags.update_tags` (see Tags.vue). */
export function useTags() {
  tagListResource ??= createListResource({
    doctype: "Tag",
    fields: ["name", "color"],
    cache: ["Tags", "Helpdesk"],
    filters: { app: "helpdesk" },
    orderBy: "name asc",
    pageLength: 500,
    auto: true,
  });

  return { tagListResource };
}
