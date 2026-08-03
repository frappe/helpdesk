/** Ordering and promotion rules for saved replies; import-free for the check file. */

export interface SavedReplyUse {
  /** Stored with the count so root rows render without fetching the list. */
  title: string;
  count: number;
}

export type SavedReplyUsage = Record<string, SavedReplyUse>;

/** Orders the drill-down on an empty query; once typed, scoring decides and this
 * is the tie-breaker. Stable sort keeps never-used replies in `modified desc`. */
export function mostUsedFirst<T extends { name: string }>(
  replies: T[],
  usage: SavedReplyUsage
): T[] {
  const count = (name: string) => usage[name]?.count ?? 0;
  return [...replies].sort((a, b) => count(b.name) - count(a.name));
}

/** Root-row promotion. The threshold makes long-tail usage degrade to nothing
 * rather than to noise. */
export function topSavedReplies(
  usage: SavedReplyUsage,
  minUses: number,
  maxRows: number
): Array<SavedReplyUse & { name: string }> {
  return Object.entries(usage)
    .filter(([, use]) => use.count >= minUses)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, maxRows)
    .map(([name, use]) => ({ name, ...use }));
}

export function withUse(
  usage: SavedReplyUsage,
  replyId: string,
  title: string
): SavedReplyUsage {
  const count = (usage[replyId]?.count ?? 0) + 1;
  return { ...usage, [replyId]: { title, count } };
}

/** Drops a reply that no longer exists, so its root row cannot fail forever. */
export function withoutReply(
  usage: SavedReplyUsage,
  replyId: string
): SavedReplyUsage {
  const { [replyId]: _gone, ...rest } = usage;
  return rest;
}
