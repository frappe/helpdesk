<template>
  <div
    class="grid p-2 py-3 items-center"
    style="grid-template-columns: 3fr 1fr"
  >
    <div class="text-ink-gray-8">{{ day.day }}</div>
    <div class="flex justify-start">
      <Switch v-model="day.active" @update:model-value="toggleDay" />
    </div>
  </div>
  <hr class="my-0.5" v-if="!props.isLast" />
</template>

<script setup lang="ts">
import { assignmentRuleData } from "@/stores/assignmentRules";
import { Switch } from "frappe-ui";

const props = defineProps({
  day: {
    type: Object,
    required: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
});

const toggleDay = (isActive) => {
  const dayIndex = assignmentRuleData.value.assignment_days.findIndex(
    (d) => d.day === props.day.day
  );

  if (isActive && dayIndex === -1) {
    assignmentRuleData.value.assignment_days.push({ day: props.day.day });
  } else {
    assignmentRuleData.value.assignment_days.splice(dayIndex, 1);
  }
};
</script>
