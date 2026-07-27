import { useTags, type Tag } from "@/composables/useTags";
import { reloadTicket, useTicket } from "@/composables/useTicket";
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

/** Already-applied tags are filtered out — this row adds, it doesn't toggle. */
export async function tagChildren(ticketId: string): Promise<Command[]> {
  const { tagListResource } = tagList();
  // Always refetch: the list is cached, and tags can be created mid-session
  // from the sidebar picker. Tags.vue reloads on open for the same reason.
  await tagListResource.reload();
  const applied = appliedTags(ticketId);
  return (tagListResource.data ?? [])
    .filter((tag: Tag) => !applied.has(tag.name))
    .map((tag: Tag) => ({
      id: `tag-${tag.name}`,
      title: tag.name,
      group: "Add tag",
      icon: LucideTags,
      perform: () => addTag(ticketId, tag),
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

async function addTag(ticketId: string, tag: Tag): Promise<void> {
  try {
    await call("helpdesk.api.tags.update_tags", {
      doctype: "HD Ticket",
      name: ticketId,
      added: [{ name: tag.name, color: tag.color || "Gray" }],
    });
    reloadTicket(ticketId);
  } catch (error: any) {
    toast.error(error?.messages?.join(", ") || __("Failed to update tags"));
  }
}
