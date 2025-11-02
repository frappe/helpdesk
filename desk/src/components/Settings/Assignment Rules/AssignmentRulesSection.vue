<template>
  <CFConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
    :disableAddCondition="props.errors !== ''"
  />
  <div
    v-if="props.conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-gray-300 text-gray-600 rounded-md"
    @click="
      props.conditions.push(['', '', '']);
      validateAssignmentRule(props.name);
    "
  >
    <FeatherIcon name="plus" class="h-4" />
    {{ __("Add a condition") }}
  </div>
  <div class="flex items-center justify-between mt-2">
    <Dropdown
      v-if="props.conditions.length > 0"
      class="mt-2"
      v-slot="{ open }"
      :options="dropdownOptions"
    >
      <Button
        :disabled="props.errors !== ''"
        :icon-right="open ? 'chevron-up' : 'chevron-down'"
        :label="__('Add condition')"
      />
    </Dropdown>
    <ErrorMessage
      v-if="props.conditions.length > 0"
      :message="props.errors"
      class="mt-2"
    />
  </div>
</template>

<script setup lang="ts">
import CFConditions from "@/components/conditions-filter/CFConditions.vue";
import { validateConditions } from "@/utils";
import { watchDebounced } from "@vueuse/core";
import { Button, Dropdown, ErrorMessage, FeatherIcon } from "frappe-ui";
import { validateAssignmentRule } from "../../../stores/assignmentRules";

const props = defineProps({
  conditions: Array<any>,
  name: String,
  errors: String,
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
    validateAssignmentRule(props.name);
  },
  { deep: true, debounce: 300 }
);
</script>
