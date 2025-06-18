<template>
  <div>
    <div class="flex text-sm text-gray-600 px-2">
      <div class="">Schedule name</div>
    </div>
    <hr class="my-2" />
    <div class="px-2">
      <div
        v-if="holidayListData.data"
        v-for="holiday in holidayListData.data"
        :key="holiday.name"
      >
        <HolidayListItem :data="holiday" />
        <hr class="my-2 -mx-2" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import HolidayListItem from "./HolidayListItem.vue";
import { holidayListData } from "./holidaylist";
</script>
