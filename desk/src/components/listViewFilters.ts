import { shallowRef } from "vue";

export type FilterCondition = [string, string, unknown];

interface ListFilterActions {
  current: () => FilterCondition[];
  apply: (filters: FilterCondition[]) => void;
}

/**
 * The mounted list's filter state, published for callers outside its provide
 * chain — the command palette lives in the sidebar and cannot inject
 * `listViewActions`. Null whenever no list is mounted.
 */
export const listFilters = shallowRef<ListFilterActions | null>(null);

/**
 * Applies `conditions` on top of what the list already has, replacing any
 * condition on the same field. Passing `[]` clears them, exactly as the filter
 * popover's "Clear all" does.
 *
 * Going through the list rather than the URL is what keeps palette filters and
 * popover filters one mechanism: same merge, same "Save Changes" affordance,
 * same persistence on a default view. Returns false when no list is mounted so
 * the caller can navigate instead.
 */
export function applyListFilters(conditions: FilterCondition[]): boolean {
  const actions = listFilters.value;
  if (!actions) return false;
  if (!conditions.length) {
    actions.apply([]);
    return true;
  }
  const overridden = new Set(conditions.map(([field]) => field));
  const kept = actions.current().filter(([field]) => !overridden.has(field));
  actions.apply([...kept, ...conditions]);
  return true;
}
