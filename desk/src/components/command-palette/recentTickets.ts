import { useStorage } from "@vueuse/core";

export interface RecentTicket {
  name: string;
  subject: string;
  visitedAt: number;
}

const MAX_RECENTS = 5;
const STORAGE_KEY = "hd_recent_tickets";

export const recentTickets = useStorage<RecentTicket[]>(STORAGE_KEY, []);

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
