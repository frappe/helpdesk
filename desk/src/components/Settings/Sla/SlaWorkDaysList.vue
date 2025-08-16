<template>
  <div class="rounded-md border px-2 border-gray-300 text-sm">
    <div
      class="grid p-2 px-4 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumnsForTable(columns),
      }"
      v-if="slaData.support_and_resolution?.length !== 0"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
        :class="{
          'ml-2': column.key === 'workday',
        }"
      >
        {{ column.label }}
        <span v-if="column.isRequired" class="text-red-500">*</span>
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
      class="text-center p-4 text-gray-600"
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
      icon-left="plus"
    />
    <ErrorMessage :message="slaDataErrors.support_and_resolution" />
  </div>
</template>

<script setup lang="ts">
import { Button } from "frappe-ui";
import SlaWorkDaysListItem from "./SlaWorkDaysListItem.vue";
import { slaData, slaDataErrors } from "@/stores/sla";
import { getGridTemplateColumnsForTable } from "@/utils";

interface Column {
  key: string;
  label: string;
  isRequired?: boolean;
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

const columns: Column[] = [
  {
    label: "Day",
    key: "workday",
    isRequired: true,
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
];
</script>
