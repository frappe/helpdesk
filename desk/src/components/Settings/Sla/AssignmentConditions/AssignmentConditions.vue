<template>
  <div class="rounded-lg border border-gray-300 p-3 flex flex-col gap-4 w-full">
    <template v-for="(condition, i) in props.conditions" :key="condition.field">
      <AssignmentCondition
        v-if="Array.isArray(condition)"
        :condition="condition"
        :doctype="'HD Ticket'"
        :isChild="props.isChild"
        :itemIndex="i"
        @remove="removeCondition(condition)"
        @unGroupConditions="unGroupConditions(condition)"
        :level="props.level + 1"
        @toggleConjunction="toggleConjunction"
        :isGroup="isGroupCondition(condition[0])"
        :conjunction="getConjunction()"
        @turnIntoGroup="turnIntoGroup(condition)"
      />
    </template>
    <div v-if="props.isChild" class="flex">
      <Dropdown v-slot="{ open }" :options="dropdownOptions">
        <Button
          :disabled="slaDataErrors.condition !== ''"
          label="Add condition"
          icon-left="plus"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
        />
      </Dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { slaDataErrors } from "@/stores/sla";
import { Button } from "frappe-ui";
import { computed, onMounted } from "vue";
import { filterableFields } from "../utils";
import AssignmentCondition from "./AssignmentCondition.vue";

const props = defineProps({
  conditions: {
    type: Array<any>,
    required: true,
  },
  isChild: {
    type: Boolean,
    default: false,
  },
  level: {
    type: Number,
    default: 0,
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

const turnIntoGroup = (condition) => {
  props.conditions.splice(props.conditions.indexOf(condition), 1, [condition]);
};

const isGroupCondition = (condition) => {
  return Array.isArray(condition);
};

const dropdownOptions = computed(() => {
  const options = [
    {
      label: "Add condition",
      onClick: () => {
        const conjunction = getConjunction();
        props.conditions.push(conjunction, ["", "", ""]);
      },
    },
  ];
  if (props.level < 3) {
    options.push({
      label: "Add condition group",
      onClick: () => {
        const conjunction = getConjunction();
        props.conditions.push(conjunction, [[]]);
      },
    });
  }
  return options;
});

function removeCondition(condition) {
  const conditionIndex = props.conditions.indexOf(condition);
  if (conditionIndex == 0) {
    props.conditions.splice(conditionIndex, 2);
  } else {
    props.conditions.splice(conditionIndex - 1, 2);
  }
}

function unGroupConditions(condition) {
  const conjunction = getConjunction();
  const newConditions = condition.map((c) => {
    if (typeof c == "string") {
      return conjunction;
    }
    return c;
  });

  const index = props.conditions.indexOf(condition);
  if (index !== -1) {
    props.conditions.splice(index, 1, ...newConditions);
  }
}

function toggleConjunction(conjunction) {
  for (let i = 0; i < props.conditions.length; i++) {
    if (typeof props.conditions[i] == "string") {
      props.conditions[i] = conjunction == "and" ? "or" : "and";
    }
  }
}

onMounted(() => {
  if (!filterableFields.fetched) {
    filterableFields.submit();
  }
});
</script>
