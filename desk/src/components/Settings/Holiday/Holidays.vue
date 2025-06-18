<template>
  <div>
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-lg font-semibold">Work schedule and holidays</h1>
        <p class="text-sm text-gray-700 mt-2 max-w-md">
          Set your team’s working days, hours, and holidays using a template or
          custom schedule.
        </p>
      </div>
      <Button
        label="Create new"
        theme="gray"
        variant="solid"
        @click="goToNew()"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <div class="mt-6">
      <HolidayList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { holidayListData, activeScreen } from "./holidaylist";
import HolidayList from "./HolidayList.vue";
import { onMounted } from "vue";

onMounted(() => {
  holidayListData.fetch();
});

const goToNew = () => {
  activeScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
