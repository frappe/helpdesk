<template>
  <div
    class="grid py-3.5 px-4 items-center"
    style="grid-template-columns: 3fr 1fr"
  >
    <div class="text-ink-gray-7 font-medium">{{ day.day }}</div>
    <div class="flex justify-start">
      <Switch v-model="day.active" @update:model-value="toggleDay" />
    </div>
  </div>
  <hr v-if="!props.isLast" />
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
  const dayIndex = assignmentRuleData.value.assignmentDays.findIndex(
    (d) => d.day === props.day.day
  );

  if (isActive && dayIndex === -1) {
    assignmentRuleData.value.assignmentDays.push({
      day: props.day.day,
    });
  } else {
    assignmentRuleData.value.assignmentDays.splice(dayIndex, 1);
  }
};
</script>
