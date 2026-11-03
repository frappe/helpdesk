<template>
  <div class="rounded-5 border px-2 border-outline-gray-2 text-sm">
    <div
      class="grid gap-2 p-2 md:px-4 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumnsForTable(columns),
      }"
      v-if="slaData.support_and_resolution?.length !== 0"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-ink-gray-5 whitespace-normal"
        :class="{
          'ms-2': column.key === 'workday',
        }"
      >
        {{ column.label }}
        <span v-if="column.isRequired" class="text-ink-red-6">*</span>
      </div>
    </div>
    <hr v-if="slaData.support_and_resolution?.length !== 0" />
    <SlaWorkDaysListItem
      v-for="(row, index) in slaData.support_and_resolution"
      :key="index + row.workday + row.id"
      :row="row"
      :columns="columns"
      :isLast="index === slaData.support_and_resolution.length - 1"
    />
    <div
      v-if="slaData.support_and_resolution?.length === 0"
      class="text-center p-4 text-ink-gray-5"
    >
      No workdays in the list
    </div>
  </div>
  <div class="flex items-center justify-between mt-2.5">
    <Button
      v-if="slaData.support_and_resolution.length < 7"
      variant="subtle"
      label="Add row"
      @click="addWorkDay"
      icon-left="lucide-plus"
    />
    <ErrorMessage :message="slaDataErrors.support_and_resolution" />
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import SlaWorkDaysListItem from "./SlaWorkDaysListItem.vue";
import { slaData, slaDataErrors } from "@/stores/sla";
import { getGridTemplateColumnsForTable } from "@/utils";
import { __ } from "@/translation";
import { useMediaQuery } from "@vueuse/core";
import { computed } from "vue";

interface Column {
  key: string;
  label: string;
  isRequired?: boolean;
  width?: number | string;
}

const allDays = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const addWorkDay = () => {
  const usedDays = new Set(
    slaData.value.support_and_resolution.map((day) => day.workday)
  );
  const nextDay = allDays.find((day) => !usedDays.has(day)) || allDays[0];

  slaData.value.support_and_resolution.push({
    workday: nextDay,
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  });
};

// Below lg a Break column squeezes the day names, so rows show the break on a second line instead.
const isWide = useMediaQuery("(min-width: 1024px)");

const columns = computed<Column[]>(() => [
  {
    label: "Day",
    key: "workday",
    isRequired: true,
    // Room for "Wednesday" in the 640px settings panel.
    width: "minmax(6.5rem, 1fr)",
  },
  {
    label: "Start time",
    key: "start_time",
    isRequired: true,
  },
  {
    label: "End time",
    key: "end_time",
    isRequired: true,
  },
  ...(isWide.value ? [{ label: __("Break"), key: "break", width: 1.7 }] : []),
]);
</script>
