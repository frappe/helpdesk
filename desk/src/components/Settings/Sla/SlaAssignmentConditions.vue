<template>
  <AssignmentConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
  />
  <div
    v-if="props.conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-gray-300 text-gray-600 rounded-md"
    @click="props.conditions.push(['', '', ''])"
  >
    <FeatherIcon name="plus" class="h-4" />
    Add a custom condition
  </div>
  <div class="flex items-center justify-between mt-2">
    <Dropdown
      v-if="props.conditions.length > 0"
      v-slot="{ open }"
      :options="dropdownOptions"
    >
      <Button
        :disabled="slaDataErrors.condition !== ''"
        :icon-right="open ? 'chevron-up' : 'chevron-down'"
        label="Add condition"
      />
    </Dropdown>
    <ErrorMessage :message="slaDataErrors.condition" />
  </div>
</template>

<script setup lang="ts">
import AssignmentConditions from "./AssignmentConditions/AssignmentConditions.vue";
import { Button, Dropdown, ErrorMessage, FeatherIcon } from "frappe-ui";
import {
  slaDataErrors,
  validateConditions,
  validateSlaData,
} from "@/stores/sla";
import { watchDebounced } from "@vueuse/core";

const props = defineProps({
  conditions: {
    type: Array<any>,
    required: true,
  },
});

const getConjunction = () => {
  let conjunction = "and";
  props.conditions.forEach((condition) => {
    if (typeof condition == "string") {
      conjunction = condition;
    }
  });
  return conjunction;
};

const dropdownOptions = [
  {
    label: "Add condition",
    onClick: () => {
      addCondition();
    },
  },
  {
    label: "Add condition group",
    onClick: () => {
      const conjunction = getConjunction();
      props.conditions.push(conjunction, [[]]);
    },
  },
];

const addCondition = () => {
  const isValid = validateConditions(props.conditions);

  if (!isValid) {
    return;
  }
  const conjunction = getConjunction();

  props.conditions.push(conjunction, ["", "", ""]);
};

watchDebounced(
  () => [...props.conditions],
  () => {
    validateSlaData("condition");
  },
  { deep: true, debounce: 100 }
);
</script>
