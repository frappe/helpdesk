<template>
  <AssignmentConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
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
      })
    "
  >
    <FeatherIcon name="plus" class="h-4" />
    Add a custom condition
  </div>
  <div class="flex items-center justify-between">
    <Dropdown
      v-if="props.conditions.length > 0"
      class="mt-2"
      v-slot="{ open }"
      :options="[
        {
          label: 'Add condition',
          onClick: () => {
            addCondition();
          },
        },
        {
          label: 'Add condition group',
          onClick: () => {
            const conjunction =
              props.conditions.length > 1
                ? props.conditions[1]?.conjunction
                : 'and';
            props.conditions.push({
              field: 'group',
              operator: 'equals',
              value: [
                {
                  field: null,
                  operator: 'equals',
                  value: '',
                  conjunction: 'and',
                },
              ],
              conjunction: conjunction,
            });
          },
        },
      ]"
    >
      <Button
        :disabled="slaDataErrors.condition !== ''"
        :icon-right="open ? 'chevron-up' : 'chevron-down'"
        label="Add condition"
      />
    </Dropdown>
    <div v-if="slaDataErrors.condition" class="text-red-500 text-xs mt-2">
      {{ slaDataErrors.condition }}
    </div>
  </div>
</template>

<script setup lang="ts">
import AssignmentConditions from "./AssignmentConditions/AssignmentConditions.vue";
import { Button, Dropdown, FeatherIcon } from "frappe-ui";
import {
  slaDataErrors,
  validateConditions,
  validateSlaData,
} from "@/stores/sla";
import { watchDebounced } from "@vueuse/core";

type Conditions = {
  field: string | object | null;
  operator: string;
  value: string | number | boolean | Array<any>;
  conjunction?: string;
};

const props = defineProps({
  conditions: {
    type: Array<Conditions>,
    required: true,
  },
});

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
    validateSlaData("condition");
  },
  { deep: true, debounce: 300 }
);
</script>
