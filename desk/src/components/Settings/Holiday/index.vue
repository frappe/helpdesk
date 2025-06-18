<template>
  <div>
    <Holidays v-if="activeScreen.screen == 'list'" />
    <HolidayListView v-else-if="activeScreen.screen == 'view'" />
  </div>
</template>

<script setup lang="ts">
import { activeScreen, holidayListData } from "./holidaylist";
import Holidays from "./Holidays.vue";
import HolidayListView from "./HolidayListView.vue";
import { onMounted } from "vue";

onMounted(() => {
  holidayListData.fetch();
});
</script>
