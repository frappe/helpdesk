import { userStorage } from "@/composables/userStorage";

export interface RecentTicket {
  name: string;
  subject: string;
  visitedAt: number;
}

const MAX_RECENTS = 3;

/** Per-agent: the unscoped key handed one shift's tickets to the next login. */
export const recentTickets = userStorage<RecentTicket[]>(
  "hd_recent_tickets",
  []
);

// Drop the pre-scoping keys already on disk (`hd_recent_commands` is a dead MRU).
["hd_recent_tickets", "hd_recent_commands"].forEach((key) =>
  localStorage.removeItem(key)
);

/** Feeds the empty-query "Recent tickets" rows. */
export function recordTicketVisit(name: string, subject: string): void {
  if (!name || !subject) return;
  const others = recentTickets.value.filter((t) => t.name !== String(name));
  recentTickets.value = [
    { name: String(name), subject, visitedAt: Date.now() },
    ...others,
  ].slice(0, MAX_RECENTS);
}
