<template>
  <div v-if="!quickFilters.loading">
    <FadedScrollableDiv
      class="flex flex-1 items-center -ml-1 flex-wrap gap-2"
      orientation="horizontal"
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
  </div>
</template>

<script setup>
import { inject } from "vue";
import { FadedScrollableDiv } from "@/components";
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

<style lang="scss" scoped></style>
