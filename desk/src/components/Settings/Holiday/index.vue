<template>
  <div class="pb-8">
    <Holidays v-if="holidayListActiveScreen.screen == 'list'" />
    <HolidayListView v-else-if="holidayListActiveScreen.screen == 'view'" />
  </div>
</template>

<script setup lang="ts">
import { holidayListActiveScreen, holidayListData } from "@/stores/holidayList";
import Holidays from "./Holidays.vue";
import HolidayListView from "./HolidayListView.vue";
import { onMounted } from "vue";

onMounted(() => {
  holidayListData.fetch();
});
</script>
