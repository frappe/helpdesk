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

function applyQuickFilter(filter, value) {
  let filters = { ...list.params?.filters };

  let field = filter.name;
  if (value) {
    if (["Check", "Select", "Link", "Date", "Datetime"].includes(filter.type)) {
      filters[field] = value;
    } else {
      filters[field] = ["LIKE", `%${value}%`];
    }
    filter["value"] = value;
  } else {
    delete filters[field];
    filter["value"] = "";
  }
  listViewActions.applyFilters(filters);
}
</script>

<style lang="scss" scoped></style>
