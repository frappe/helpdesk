import { useTags, type Tag } from "@/composables/useTags";
import { useTicket } from "@/composables/useTicket";
import { __ } from "@/translation";
import { call, toast } from "frappe-ui";
import type { Command } from "./paletteTypes";

import LucideTags from "~icons/lucide/tags";

/** Toggle list: applied tags ticked; Enter flips one and pops back a level. */
export async function tagChildren(ticketId: string): Promise<Command[]> {
  const { tagListResource } = useTags();
  // Always refetch: tags can be created mid-session from the sidebar picker.
  await tagListResource.reload();
  const applied = appliedTags(ticketId);
  return (tagListResource.data ?? []).map((tag: Tag) => ({
    id: `tag-${tag.name}`,
    title: tag.name,
    group: "Tags",
    icon: LucideTags,
    checked: applied.has(tag.name),
    keepOpen: true,
    perform: () => toggleTag(ticketId, tag),
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

/** Applied state is read at call time, so toggling the same row twice works. */
async function toggleTag(ticketId: string, tag: Tag): Promise<void> {
  const applied = appliedTags(ticketId).has(tag.name);
  try {
    const userTags = await call("helpdesk.api.tags.update_tags", {
      doctype: "HD Ticket",
      name: ticketId,
      added: applied ? [] : [{ name: tag.name, color: tag.color || "Gray" }],
      removed: applied ? [tag.name] : [],
    });
    const { ticket, activities } = useTicket(ticketId);
    // The response carries the new _user_tags: one round trip, no doc reload.
    if (ticket.doc) ticket.doc._user_tags = userTags;
    activities.reload();
  } catch (error: any) {
    toast.error(error?.messages?.join(", ") || __("Failed to update tags"));
    throw error; // the palette flips the optimistic tick back
  }
}
