<template>
  <FadedScrollableDiv
    class="quick-filters flex flex-1 items-center overflow-x-auto py-1 gap-2 pe-4 ps-1 -ms-1"
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
import { normalizeFilters } from "./filter";
import QuickFilterField from "./QuickFilterField.vue";

const listViewData = inject("listViewData");
const listViewActions = inject("listViewActions");
const { list, quickFilters } = listViewData;

const directValueFilterTypes = ["Check", "Select", "Link", "Date", "Datetime"];

function applyQuickFilter(filter, value) {
  const conditions = normalizeFilters(list.params?.filters).filter(
    (condition) => condition[0] !== filter.name
  );
  if (value) {
    if (directValueFilterTypes.includes(filter.type)) {
      conditions.push([filter.name, "=", value]);
    } else {
      conditions.push([filter.name, "LIKE", `%${value}%`]);
    }
  }
  listViewActions.applyFilters(conditions);
}

function getDefaultValue(quickFilter) {
  return quickFilter.type === "Check" ? false : "";
}

function getValue(quickFilter, filters) {
  if (!(quickFilter && quickFilter.name)) {
    return getDefaultValue(quickFilter);
  }
  const condition = normalizeFilters(filters).find(
    (c) => c[0] === quickFilter.name
  );
  if (!condition) {
    return getDefaultValue(quickFilter);
  }
  const [, operator, value] = condition;
  if (directValueFilterTypes.includes(quickFilter.type)) {
    return operator === "=" ? value : getDefaultValue(quickFilter);
  }
  if (String(operator).toLowerCase() !== "like" || typeof value !== "string") {
    return getDefaultValue(quickFilter);
  }
  return value.replaceAll("%", "");
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
