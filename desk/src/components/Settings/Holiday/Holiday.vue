<template>
  <Holidays v-if="holidayListActiveScreen.screen == 'list'" />
  <HolidayView v-else-if="holidayListActiveScreen.screen == 'view'" />
</template>

<script setup lang="ts">
import { holidayListActiveScreen } from "@/stores/holidayList";
import Holidays from "./Holidays.vue";
import HolidayView from "./HolidayView.vue";
import { createListResource } from "frappe-ui";
import { onUnmounted, provide, ref } from "vue";
import { HolidayListResourceSymbol } from "@/types";

const holidayListData = createListResource({
  doctype: "HD Service Holiday List",
  fields: ["name", "description"],
  cache: ["HolidayList"],
  orderBy: "modified desc",
  start: 0,
  pageLength: 999,
  auto: true,
});
const holidaySearchRef = ref("");

provide("holidaySearchRef", holidaySearchRef);
provide(HolidayListResourceSymbol, holidayListData);

onUnmounted(() => {
  holidaySearchRef.value = "";
  holidayListData.filters = {};
});
</script>
