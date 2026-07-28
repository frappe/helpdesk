import { useTags, type Tag } from "@/composables/useTags";
import { useTicket } from "@/composables/useTicket";
import { __ } from "@/translation";
import { call, toast } from "frappe-ui";
import type { Command } from "./paletteTypes";

import LucideTags from "~icons/lucide/tags";

// useTags() mints a resource per call; hold one so drilling in twice doesn't.
let tags: ReturnType<typeof useTags> | null = null;
function tagList() {
  if (!tags) tags = useTags();
  return tags;
}

/**
 * A toggle list, the way Linear's label picker works: every tag listed, applied
 * ones ticked, Enter flips one without closing — several tags in one visit.
 */
export async function tagChildren(ticketId: string): Promise<Command[]> {
  const { tagListResource } = tagList();
  // Always refetch: the list is cached, and tags can be created mid-session
  // from the sidebar picker. Tags.vue reloads on open for the same reason.
  await tagListResource.reload();
  const applied = appliedTags(ticketId);
  return (tagListResource.data ?? []).map((tag: Tag) => ({
    id: `tag-${tag.name}`,
    title: tag.name,
    group: "Tags",
    icon: LucideTags,
    checked: applied.has(tag.name),
    keepOpen: true,
    perform: () => toggleTag(ticketId, tag, applied.has(tag.name)),
  }));
}

/** `_user_tags` is a comma-joined column, sometimes with a leading comma. */
function appliedTags(ticketId: string): Set<string> {
  const raw = useTicket(ticketId).ticket.doc?._user_tags ?? "";
  return new Set(
    raw
      .split(",")
      .map((tag: string) => tag.trim())
      .filter(Boolean)
  );
}

async function toggleTag(
  ticketId: string,
  tag: Tag,
  applied: boolean
): Promise<void> {
  try {
    await call("helpdesk.api.tags.update_tags", {
      doctype: "HD Ticket",
      name: ticketId,
      added: applied ? [] : [{ name: tag.name, color: tag.color || "Gray" }],
      removed: applied ? [tag.name] : [],
    });
    const { ticket, activities } = useTicket(ticketId);
    activities.reload();
    await ticket.reload(); // the rebuilt level reads its ticks from the doc
  } catch (error: any) {
    toast.error(error?.messages?.join(", ") || __("Failed to update tags"));
  }
}
