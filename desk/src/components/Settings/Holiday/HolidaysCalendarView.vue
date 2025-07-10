<template>
  <div class="p-3 rounded-md border border-gray-300">
    <div class="mb-6 flex justify-between items-center">
      <div class="ml-2">
        <YearsList
          v-if="startYear !== endYear"
          v-model="currentYear"
          :startYear="startYear"
          :endYear="endYear"
        >
          <template #trigger="{ toggle, selectedYear }">
            <div
              class="flex items-center gap-2 font-semibold text-xl cursor-pointer select-none"
              @click="toggle"
            >
              {{ selectedYear }}
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </template>
        </YearsList>
        <div
          v-else
          class="flex items-center gap-2 font-semibold text-xl select-none"
        >
          {{ startYear }}
        </div>
      </div>
      <div class="flex gap-2 items-center">
        <Button
          variant="ghost"
          icon="chevron-left"
          :disabled="visibleMonths === 'first-half'"
          @click="visibleMonths = 'first-half'"
        />
        <Button variant="ghost" label="Today" @click="goToToday()" />
        <Button
          variant="ghost"
          icon="chevron-right"
          :disabled="visibleMonths === 'second-half'"
          @click="visibleMonths = 'second-half'"
        />
      </div>
    </div>
    <div
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
      v-if="visibleMonths === 'first-half'"
    >
      <HLCalender
        v-for="month in months.slice(0, 6)"
        :key="month"
        :year="currentYear"
        :month="month"
        :holidays="holidayData.holidays"
      />
    </div>
    <div
      class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 justify-between gap-5"
      v-else
    >
      <HLCalender
        v-for="month in months.slice(6, 12)"
        :key="month"
        :year="currentYear"
        :month="month"
        :holidays="holidayData.holidays"
      />
    </div>
    <div class="flex gap-2 items-center w-full justify-center mt-8">
      <div
        :class="[
          'size-1.5 rounded-full cursor-pointer',
          {
            'bg-black': visibleMonths === 'first-half',
            'bg-gray-400': visibleMonths === 'second-half',
          },
        ]"
        @click="visibleMonths = 'first-half'"
      />
      <div
        :class="[
          'size-1.5 rounded-full cursor-pointer',
          {
            'bg-black': visibleMonths === 'second-half',
            'bg-gray-400': visibleMonths === 'first-half',
          },
        ]"
        @click="visibleMonths = 'second-half'"
      />
    </div>
  </div>
  <AddHolidayModal v-model="dialog" />
</template>
<script setup lang="ts">
import { ref, watch } from "vue";
import HLCalender from "./HLCalender.vue";
import YearsList from "./YearsList.vue";
import dayjs from "dayjs";
import { holidayData } from "@/stores/holidayList";

const visibleMonths = ref<"first-half" | "second-half">("first-half");
const months = ref([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
const currentYear = ref(dayjs().year());
const dialog = ref(false);
const startYear = ref(dayjs(holidayData.value.from_date || dayjs()).year());
const endYear = ref(dayjs(holidayData.value.to_date || dayjs()).year());

const goToToday = () => {
  const today = dayjs();
  currentYear.value = today.year();
  visibleMonths.value = today.month() >= 6 ? "second-half" : "first-half";
};

watch(
  () => [holidayData.value.from_date, holidayData.value.to_date],
  ([fromDate, toDate]) => {
    fromDate = dayjs(fromDate);
    toDate = dayjs(toDate);
    startYear.value = fromDate.year();
    endYear.value = toDate.year();
    currentYear.value = fromDate.year();
    visibleMonths.value = fromDate.month() >= 6 ? "second-half" : "first-half";
  }
);
</script>
