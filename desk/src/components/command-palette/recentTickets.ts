import { userStorage } from "./userStorage";

export interface RecentTicket {
  name: string;
  subject: string;
  visitedAt: number;
}

const MAX_RECENTS = 5;

/**
 * Per-agent: subjects routinely carry customer names, and the unscoped key
 * handed the previous shift's tickets to whoever logged in next.
 */
export const recentTickets = userStorage<RecentTicket[]>(
  "hd_recent_tickets",
  []
);

// Scoping the key stops the next leak; these drop the one already on disk.
// `hd_recent_commands` belonged to the deleted command MRU.
["hd_recent_tickets", "hd_recent_commands"].forEach((key) =>
  localStorage.removeItem(key)
);

/**
 * Records a ticket visit so the palette can show "what you'd probably do next"
 * on an empty query instead of a static nav list.
 */
export function recordTicketVisit(name: string, subject: string): void {
  if (!name || !subject) return;
  const others = recentTickets.value.filter((t) => t.name !== String(name));
  recentTickets.value = [
    { name: String(name), subject, visitedAt: Date.now() },
    ...others,
  ].slice(0, MAX_RECENTS);
}
