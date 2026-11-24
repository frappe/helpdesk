import {
  groupsByAssignee,
  serializeGroupBy,
  serializeGroupByTotals,
  splitAssignees,
} from "@framework/ui/GroupBy";
import type { GroupBySettings } from "@framework/ui/GroupBy";
import { createResource } from "frappe-ui";
import { computed, MaybeRefOrGetter, ref, toValue, watch } from "vue";

// most lists of assignees fetched when grouped by assignee
const ASSIGNEE_CAP = 1000;

// useGroupByData through get_grouped_list, so @me and assigned-on filters match the list
export function useGroupedList(
  doctype: MaybeRefOrGetter<string>,
  groupBy: MaybeRefOrGetter<GroupBySettings | null>,
  filters: MaybeRefOrGetter<unknown>
) {
  const pageLength = ref(20);
  const start = ref(0);
  const loaded = ref<Record<string, unknown>[]>([]);
  const lastPageFull = ref(false);
  // grouped by assignee, every group is fetched at once and paged here
  const shown = ref(pageLength.value);
  const url = "helpdesk.api.doc.get_grouped_list";

  const grouping = () => toValue(groupBy) as GroupBySettings;
  const splitsLocally = () => {
    const settings = toValue(groupBy);
    return Boolean(settings && groupsByAssignee(settings));
  };
  const base = () => ({ doctype: toValue(doctype), filters: toValue(filters) });

  // Load More fetches only the next page, like desk's report view, so groups are never counted.
  const groups = createResource({
    url,
    makeParams: () => ({
      ...base(),
      ...serializeGroupBy(grouping()),
      limit_start: start.value,
      limit_page_length: splitsLocally() ? ASSIGNEE_CAP : pageLength.value,
    }),
    onSuccess(data: Record<string, unknown>[]) {
      loaded.value = start.value ? [...loaded.value, ...data] : data;
      lastPageFull.value = data.length === pageLength.value;
    },
  });

  const totals = createResource({
    url,
    makeParams: () => ({
      ...base(),
      ...serializeGroupByTotals(grouping()),
      limit_page_length: 1,
    }),
  });

  const wantsTotals = (settings: GroupBySettings | null) =>
    Boolean(settings?.showTotals && serializeGroupByTotals(settings));

  function reloadGroups() {
    if (!toValue(groupBy)) return;
    start.value = 0;
    shown.value = pageLength.value;
    groups.fetch();
  }

  function reload() {
    reloadGroups();
    if (wantsTotals(toValue(groupBy))) totals.fetch();
  }

  function loadMore() {
    if (!toValue(groupBy)) return;
    if (splitsLocally()) {
      shown.value += pageLength.value;
      return;
    }
    start.value = loaded.value.length;
    groups.fetch();
  }

  // Column widths live on the grouping too; only what reaches the query refetches.
  const query = computed(() => {
    const settings = toValue(groupBy);
    if (!settings) return null;
    return JSON.stringify([serializeGroupBy(settings), settings.showTotals]);
  });

  watch([() => toValue(doctype), query, () => toValue(filters)], reload, {
    immediate: true,
    deep: true,
  });
  // the totals don't depend on the page size
  watch(pageLength, reloadGroups);

  const error = computed(
    () =>
      groups.error || (wantsTotals(toValue(groupBy)) && totals.error) || null
  );
  // after a failed fetch, show the error rather than the previous groups
  const splitGroups = computed(() =>
    splitsLocally() ? splitAssignees(loaded.value, grouping()) : []
  );
  const rows = computed<Record<string, unknown>[]>(() => {
    if (!toValue(groupBy) || error.value) return [];
    return splitsLocally()
      ? splitGroups.value.slice(0, shown.value)
      : loaded.value;
  });

  return {
    rows,
    totals: computed(() =>
      wantsTotals(toValue(groupBy)) && !error.value
        ? totals.data?.[0] ?? null
        : null
    ),
    loading: computed(() => Boolean(groups.loading)),
    error,
    rowCount: computed(() => rows.value.length),
    hasNextPage: computed(() =>
      splitsLocally()
        ? shown.value < splitGroups.value.length
        : lastPageFull.value
    ),
    pageLength,
    loadMore,
    reload,
  };
}
