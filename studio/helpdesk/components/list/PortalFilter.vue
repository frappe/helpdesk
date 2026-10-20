<template>
  <Filter />
</template>

<script setup lang="ts">
import { computed, provide, reactive } from "vue";
import {
  parseFilters,
  serializeFilters,
} from "@framework/ui/components/Filter/filters";
import { Filter } from "@helpdesk/shared/filter";

// The desk's Filter injects these, as ListViewBuilder provides them.
const props = defineProps<{ fields?: any[] }>();
const conditions = defineModel<any[]>({ default: () => [] });

// `value` as the desk's get_filterable_fields adds it.
const fields = computed(() =>
  (props.fields || []).map((field) => ({
    label: field.label,
    value: field.fieldname,
    ...field,
  }))
);

provide("listViewData", {
  list: reactive({
    params: { filters: computed(() => serializeFilters(conditions.value)) },
  }),
  filterableFields: reactive({ data: fields }),
});
provide("listViewActions", {
  applyFilters: (wire) =>
    (conditions.value = parseFilters(withUnlisted(wire), wire).map(
      ({ fieldname, operator, value }) => ({
        fieldname,
        operator,
        value,
      })
    )),
});

// parseFilters drops unlisted fields, e.g. the org switcher's `customer`.
function withUnlisted(wire) {
  const listed = new Set(fields.value.map((field) => field.fieldname));
  const unlisted = wire
    .filter(([fieldname]) => !listed.has(fieldname))
    .map(([fieldname]) => ({ fieldname, fieldtype: "Data" }));
  return [...fields.value, ...unlisted];
}
</script>
