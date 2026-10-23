<template>
  <Filter />
</template>

<script setup lang="ts">
import { computed, provide, reactive } from "vue";
import { serializeFilters } from "@framework/ui/components/Filter/filters";
import { Filter, toConditions } from "@helpdesk/shared/filter";

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
// Keeps unlisted fields, e.g. the org switcher's `customer`.
provide("listViewActions", {
  applyFilters: (wire) => (conditions.value = toConditions(wire, fields.value)),
});
</script>
