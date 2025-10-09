<template>
  <div
    v-if="holidayList.list.loading && !holidayList.list.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else class="-ml-2">
    <div
      v-if="!holidayList.list.loading && !holidayList.list.data?.length"
      class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <Briefcase class="size-6 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base font-medium text-ink-gray-6">
          No Holiday list found
        </div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          Add your first Holiday list to get started.
        </div>
      </div>
      <Button
        label="Add Holiday"
        variant="outline"
        icon-left="plus"
        @click="goToNew()"
      />
    </div>
    <div v-else>
      <div class="flex text-sm text-gray-600">
        <div class="ml-2">Schedule name</div>
      </div>
      <hr class="mx-2 mt-2" />
      <div>
        <div v-for="holiday in holidayList.list.data" :key="holiday.name">
          <HolidayListItem :data="holiday" />
          <hr class="mx-2" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import HolidayListItem from "./HolidayListItem.vue";
import { LoadingIndicator } from "frappe-ui";
import Briefcase from "~icons/lucide/briefcase";

import { inject } from "vue";
import {
  holidayListActiveScreen,
  resetHolidayData,
} from "@/stores/holidayList";

const holidayList = inject<any>("holidayList");

const goToNew = () => {
  resetHolidayData();
  holidayListActiveScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
