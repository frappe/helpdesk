<template>
  <FadedScrollableDiv
    class="quick-filters flex flex-1 items-center overflow-x-auto py-1 gap-2 pr-4"
    orientation="horizontal"
    v-if="!quickFilters.loading"
  >
    <div
      v-for="filter in quickFilters.data"
      :key="filter.name"
      class="min-w-36"
    >
      <QuickFilterField
        :filter="filter"
        :value="getValue(filter, list.params?.filters)"
        @applyQuickFilter="(f, v) => applyQuickFilter(f, v)"
      />
    </div>
  </FadedScrollableDiv>
</template>

<script setup>
import { FadedScrollableDiv } from "@/components";
import { inject } from "vue";
import QuickFilterField from "./QuickFilterField.vue";

const listViewData = inject("listViewData");
const listViewActions = inject("listViewActions");
const { list, quickFilters } = listViewData;

const directValueFilterTypes = ["Check", "Select", "Link", "Date", "Datetime"];

function applyQuickFilter(filter, value) {
  let filters = { ...list.params?.filters };

  let field = filter.name;
  if (value) {
    if (directValueFilterTypes.includes(filter.type)) {
      filters[field] = value;
    } else {
      filters[field] = ["LIKE", `%${value}%`];
    }
  } else {
    delete filters[field];
  }
  listViewActions.applyFilters(filters);
}

function getDefaultValue(quickFilter) {
  return quickFilter.type === "Check" ? false : "";
}

function getValue(quickFilter, filters) {
  if (!filters || !(quickFilter && quickFilter.name)) {
    return getDefaultValue(quickFilter);
  }
  const filter = filters[quickFilter.name];
  if (filter === undefined) {
    // not a part of the customizable filters
    return getDefaultValue(quickFilter);
  }
  if (directValueFilterTypes.includes(quickFilter.type)) {
    return filter;
  }
  if (
    !Array.isArray(filter) ||
    filter.length !== 2 ||
    filter[0].toLowerCase() !== "like"
  ) {
    return getDefaultValue(quickFilter);
  }
  let value = filter[1];
  if (value.startsWith("%")) {
    value = value.substring(1);
  }
  if (value.endsWith("%")) {
    value = value.substring(0, value.length - 1);
  }
  return value;
}
</script>

<style scoped>
.quick-filters {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}
.quick-filters::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}
</style>
