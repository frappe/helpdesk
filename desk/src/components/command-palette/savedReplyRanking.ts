/**
 * Ordering and promotion rules for saved replies, kept free of imports so they
 * can be exercised by `savedReplyRanking.check.ts` without Vue or a browser.
 */

export interface SavedReplyUse {
  /** Stored with the count so root rows render without fetching the list. */
  title: string;
  count: number;
}

export type SavedReplyUsage = Record<string, SavedReplyUse>;

/**
 * Most-used first. Callers apply this to the drill-down list, where it orders
 * rows on an **empty query only** — once the agent types, `scoreCommand` decides
 * and this survives as the tie-breaker, because `groupCommands` falls back to
 * source order at equal score.
 *
 * `sort` is stable, so never-used replies keep the order they arrived in
 * (`modified desc`), which is the cold-start order for an agent with no history.
 */
export function mostUsedFirst<T extends { name: string }>(
  replies: T[],
  usage: SavedReplyUsage
): T[] {
  const count = (name: string) => usage[name]?.count ?? 0;
  return [...replies].sort((a, b) => count(b.name) - count(a.name));
}

/**
 * The replies that have earned a root-level row. A threshold rather than a
 * guess: an agent whose usage is long-tail never accumulates a qualifying reply
 * and sees nothing at root, which is the right outcome for them — the feature
 * degrades to nothing rather than to noise.
 */
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
