import {
  serializeGroupBy,
  serializeGroupByTotals,
} from "@framework/ui/GroupBy";
import type { GroupBySettings } from "@framework/ui/GroupBy";
import { createResource } from "frappe-ui";
import { computed, MaybeRefOrGetter, ref, toValue, watch } from "vue";

// Most group keys fetched to count the groups; past it the total is a floor.
const COUNT_CAP = 1000;

// useGroupByData through get_grouped_list, so @me and assigned-on filters match the list
export function useGroupedList(
  doctype: MaybeRefOrGetter<string>,
  groupBy: MaybeRefOrGetter<GroupBySettings | null>,
  filters: MaybeRefOrGetter<unknown>
) {
  const pageLength = ref(20);
  const limit = ref(pageLength.value);
  const url = "helpdesk.api.doc.get_grouped_list";

  const grouping = () => toValue(groupBy) as GroupBySettings;
  const base = () => ({ doctype: toValue(doctype), filters: toValue(filters) });

  const groups = createResource({
    url,
    makeParams: () => ({
      ...base(),
      ...serializeGroupBy(grouping()),
      limit_page_length: limit.value,
    }),
  });

  // The group fields alone, one row per group, to count them.
  const groupKeys = createResource({
    url,
    makeParams: () => {
      const { fields, group_by } = serializeGroupBy({
        ...grouping(),
        aggregates: [],
      });
      return { ...base(), fields, group_by, limit_page_length: COUNT_CAP };
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

  function reload() {
    const settings = toValue(groupBy);
    if (!settings) return;
    limit.value = pageLength.value;
    groups.fetch();
    groupKeys.fetch();
    if (wantsTotals(settings)) totals.fetch();
  }

  function loadMore() {
    if (!toValue(groupBy)) return;
    limit.value += pageLength.value;
    groups.fetch();
  }

  // Column widths live on the grouping too; only what reaches the query refetches.
  const query = computed(() => {
    const settings = toValue(groupBy);
    if (!settings) return null;
    return JSON.stringify([serializeGroupBy(settings), settings.showTotals]);
  });

  watch(
    [() => toValue(doctype), query, () => toValue(filters), pageLength],
    reload,
    { immediate: true, deep: true }
  );

  const error = computed(
    () =>
      groups.error ||
      groupKeys.error ||
      (wantsTotals(toValue(groupBy)) && totals.error) ||
      null
  );
  // after a failed fetch, show the error rather than the previous groups
  const rows = computed<Record<string, unknown>[]>(() =>
    toValue(groupBy) && !error.value ? groups.data ?? [] : []
  );
  const totalCount = computed<number>(() => groupKeys.data?.length ?? 0);
  const totalCapped = computed(() => totalCount.value >= COUNT_CAP);

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
    totalCount,
    totalCapped,
    // past a capped total, a full page is the only sign more groups exist
    hasNextPage: computed(() =>
      totalCapped.value
        ? rows.value.length >= limit.value
        : rows.value.length < totalCount.value
    ),
    pageLength,
    loadMore,
    reload,
  };
}
