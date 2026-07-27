import TicketPriority from "@/components/TicketPriority.vue";
import { router } from "@/router";
import { GROUP, stripTags, type Command, type SearchItem } from "./paletteTypes";

/**
 * Server-side full-text hits, mapped onto the same row shape. They keep the
 * server's relevance order via `rank` instead of being re-scored locally.
 */
export function searchCommands(items: SearchItem[]): Command[] {
  return items.map((item, index) => ({
    id: `search-${item.doctype}-${item.name}`,
    title: stripTags(item.title || item.content || item.name),
    subtitle: searchSubtitle(item),
    // Priority up front, status in the subtitle: repeated subjects are common,
    // and the index returns both, so neither has to be guessed at.
    icon: TicketPriority,
    iconProps: { priority: item.priority, iconOnly: true },
    group: GROUP.results,
    rank: 950 - index,
    perform: () => router.push(routeForSearchItem(item)),
  }));
}

/** "Open · #0484" — enough to tell apart tickets sharing a subject. */
function searchSubtitle(item: SearchItem): string {
  const ticketId = ticketIdOf(item);
  return [item.status, ticketId && `#${ticketId}`].filter(Boolean).join(" · ");
}

function ticketIdOf(item: SearchItem): string {
  if (item.doctype === "HD Ticket") return item.name;
  return item.reference_ticket || item.reference_name || "";
}

function routeForSearchItem(item: SearchItem) {
  const ticketId = ticketIdOf(item);
  if (item.doctype === "HD Ticket") {
    return { name: "TicketAgent", params: { ticketId } };
  }
  const prefix =
    item.doctype === "HD Ticket Comment" ? "comment" : "communication";
  return {
    name: "TicketAgent",
    params: { ticketId },
    hash: "#activity",
    query: { highlight: `${prefix}-${item.name}` },
  };
}
