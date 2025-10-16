<template>
  <div class="rounded-md border px-2 border-gray-300 text-sm">
    <div
      class="grid p-2 px-4 items-center"
      style="grid-template-columns: 3fr 1fr"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
      </div>
    </div>
    <hr />
    <AssignmentScheduleItem
      v-for="(day, index) in days"
      :key="day.day"
      :data="day"
      :isLast="index === days.length - 1"
    />
  </div>
  <ErrorMessage :message="assignmentRulesErrors.assignmentDays" class="mt-2" />
</template>

<script setup lang="ts">
import { ErrorMessage } from "frappe-ui";
import { onMounted, ref } from "vue";
import {
  assignmentRuleData,
  assignmentRulesErrors,
} from "@/stores/assignmentRules";
import AssignmentScheduleItem from "./AssignmentScheduleItem.vue";
import { __ } from "@/translation";

const columns = [
  {
    label: __("Days"),
    key: "day",
  },
  {
    label: __("Active"),
    key: "active",
  },
];

const days = ref([
  {
    day: __("Monday"),
    active: false,
  },
  {
    day: __("Tuesday"),
    active: false,
  },
  {
    day: __("Wednesday"),
    active: false,
  },
  {
    day: __("Thursday"),
    active: false,
  },
  {
    day: __("Friday"),
    active: false,
  },
  {
    day: __("Saturday"),
    active: false,
  },
  {
    day: __("Sunday"),
    active: false,
  },
]);

onMounted(() => {
  assignmentRuleData.value.assignmentDays.forEach((day) => {
    const workDay = days.value.find((d) => d.day === day);
    if (workDay) {
      workDay.active = true;
    }
  });
});
</script>
