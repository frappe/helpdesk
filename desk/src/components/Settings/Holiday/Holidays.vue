<template>
  <div class="px-10 py-8 overflow-y-auto h-full">
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">Business Holidays</h1>
        <p class="text-sm max-w-lg leading-5 text-ink-gray-6">
          Set your team’s working days, hours, and holidays using a template or
          custom schedule.
        </p>
      </div>
      <Button
        label="New"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </div>
    <div class="mt-6">
      <HolidayList />
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  holidayListActiveScreen,
  resetHolidayData,
} from "@/stores/holidayList";
import { createListResource } from "frappe-ui";
import { provide } from "vue";
import HolidayList from "./HolidayList.vue";

const holidayListData = createListResource({
  doctype: "HD Service Holiday List",
  fields: ["*"],
  orderBy: "creation desc",
  start: 0,
  pageLength: 999,
  auto: true,
});

provide("holidayList", holidayListData);

const goToNew = () => {
  resetHolidayData();
  holidayListActiveScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
