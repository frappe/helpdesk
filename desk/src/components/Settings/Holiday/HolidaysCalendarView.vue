<template>
  <div class="p-3 rounded-md border border-gray-300">
    <div class="mb-6 flex justify-between items-center">
      <div class="ml-2">
        <YearsList
          v-if="
            dayjs(holidayData.from_date || new Date()).year() !==
            dayjs(holidayData.to_date || new Date()).year()
          "
          v-model="currentYear"
          :startYear="dayjs(holidayData.from_date || new Date()).year()"
          :endYear="dayjs(holidayData.to_date || new Date()).year()"
          @update:modelValue="visibleMonths = 'first-half'"
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
          {{ dayjs(holidayData.from_date || new Date()).year() }}
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
    <div class="grid grid-cols-3 gap-5" v-if="visibleMonths === 'first-half'">
      <HLCalender
        v-for="month in months.slice(0, 6)"
        :key="month"
        :year="currentYear"
        :month="month"
        :holidays="holidayData.holidays"
      />
    </div>
    <div class="grid grid-cols-3 gap-5" v-else>
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
  <AddHolidayModal
    v-model="dialog"
    :holidays="holidayData.holidays"
    :from_date="holidayData.from_date"
    :to_date="holidayData.to_date"
  />
</template>
<script setup lang="ts">
import { ref } from "vue";
import HLCalender from "./HLCalender.vue";
import YearsList from "./YearsList.vue";
import dayjs from "dayjs";
import { holidayData } from "./holidayList";

const visibleMonths = ref<"first-half" | "second-half">("first-half");
const months = ref([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]);
const currentYear = ref(new Date().getFullYear());
const dialog = ref(false);

const goToToday = () => {
  const today = new Date();
  currentYear.value = today.getFullYear();
  visibleMonths.value = today.getMonth() >= 6 ? "second-half" : "first-half";
};
</script>
