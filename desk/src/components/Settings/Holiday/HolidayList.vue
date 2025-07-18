<template>
  <div
    v-if="holidayList.list.loading && !holidayList.list.data"
    class="flex items-center justify-center mt-12"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else>
    <div
      v-if="holidayList.list.data?.length === 0"
      class="flex items-center justify-center rounded-md border border-gray-200 p-4"
    >
      <div class="text-sm text-ink-gray-7">No items in the list</div>
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

import { inject } from "vue";

const holidayList = inject<any>("holidayList");
</script>
