<template>
  <Filter />
</template>

<script setup lang="ts">
import { computed, provide, reactive } from "vue";
import { parseFilters, serializeFilters } from "@framework/ui/components/Filter/filters";
import { Filter } from "@helpdesk/shared/filter";

// The desk's filter, fed the way ListViewBuilder feeds it: the list's conditions in Frappe's
// `[field, operator, value]` form, and a setter. The page keeps them in the UI form its views save.
const props = defineProps<{ fields?: any[] }>();
const conditions = defineModel<any[]>({ default: () => [] });

// Rows carry `value` as well as `fieldname`, as the desk's get_filterable_fields transform adds.
const fields = computed(() =>
  (props.fields || []).map((field) => ({ label: field.label, value: field.fieldname, ...field })),
);

provide("listViewData", {
  list: reactive({ params: { filters: computed(() => serializeFilters(conditions.value)) } }),
  filterableFields: reactive({ data: fields }),
});
provide("listViewActions", {
  // Stored without the field's meta, like the quick filters and organization switcher store theirs.
  applyFilters: (wire) =>
    (conditions.value = parseFilters(withUnlisted(wire), wire).map(({ fieldname, operator, value }) => ({
      fieldname,
      operator,
      value,
    }))),
});

// The organization switcher filters on `customer`, which the filter may not list; parsing drops a
// condition on an unknown field, so it would vanish with the next change.
function withUnlisted(wire) {
  const listed = new Set(fields.value.map((field) => field.fieldname));
  const unlisted = wire
    .filter(([fieldname]) => !listed.has(fieldname))
    .map(([fieldname]) => ({ fieldname, fieldtype: "Data" }));
  return [...fields.value, ...unlisted];
}
</script>
