<template>
  <AssignmentConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
    :errors="props.errors"
  />
  <div
    v-if="props.conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-gray-300 text-gray-600 rounded-md"
    @click="
      props.conditions.push({
        field: null,
        operator: 'equals',
        value: '',
        conjunction: 'and',
      });
      validateAssignmentRule(props.name);
    "
  >
    <FeatherIcon name="plus" class="h-4" />
    Add a condition
  </div>
  <div class="flex items-center justify-between">
    <Dropdown
      v-if="props.conditions.length > 0"
      class="mt-2"
      v-slot="{ open }"
      :options="dropdownOptions"
    >
      <Button
        :disabled="props.errors !== ''"
        :icon-right="open ? 'chevron-up' : 'chevron-down'"
        label="Add condition"
      />
    </Dropdown>
    <div v-if="props.errors" class="text-red-500 text-xs mt-2">
      {{ props.errors }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, Dropdown, FeatherIcon } from "frappe-ui";
import { watchDebounced } from "@vueuse/core";
import {
  validateAssignmentRule,
  validateConditions,
} from "../../../stores/assignmentRules";
import AssignmentConditions from "./Assignment Conditions/AssignmentConditions.vue";

const props = defineProps({
  conditions: Array<any>,
  name: String,
  errors: String,
});

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
      const conjunction =
        props.conditions.length > 1 ? props.conditions[1]?.conjunction : "and";
      props.conditions.push({
        field: "group",
        operator: "equals",
        value: [
          {
            field: null,
            operator: "equals",
            value: "",
            conjunction: "and",
          },
        ],
        conjunction: conjunction,
      });
    },
  },
];

const addCondition = () => {
  const isValid = validateConditions(props.conditions);

  if (!isValid) {
    return;
  }
  const conjunction =
    props.conditions.length > 1 ? props.conditions[1]?.conjunction : "and";

  props.conditions.push({
    field: null,
    operator: "equals",
    value: "",
    conjunction: conjunction,
  });
};

watchDebounced(
  () => [...props.conditions],
  () => {
    validateAssignmentRule(props.name);
  },
  { deep: true, debounce: 300 }
);
</script>
