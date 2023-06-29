<template>
  <Dropdown
    :options="options"
    :button="{
      label,
      iconRight: 'chevron-down',
      variant: 'outline',
      size: 'sm',
    }"
  />
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Dropdown } from "frappe-ui";
import { createListManager } from "@/composables/listManager";
import { useListFilters } from "@/composables/listFilters";
import { useConfigStore } from "@/stores/config";

const route = useRoute();
const listFilters = useListFilters();
const configStore = useConfigStore();
const label = ref("All Tickets");

const res = createListManager({
  doctype: "HD Preset Filter",
  fields: [
    "name",
    "title",
    "type",
    { filters: ["label", "fieldname", "filter_type", "value"] },
  ],
  auto: true,
});

const options = computed(() =>
  res.data?.map((f) => {
    const query = listFilters.toQuery(f.filters);
    const { q } = route.query;
    if (query === q) label.value = f.title;

    return {
      label: f.title,
      onClick: () => listFilters.applyQuery(query),
    };
  })
);

watch(label, (l: string) => configStore.setTitle(l), { immediate: true });
onBeforeUnmount(() => configStore.setTitle());
</script>
