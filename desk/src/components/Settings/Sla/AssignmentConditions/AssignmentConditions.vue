<template>
  <div
    class="rounded-lg border border-gray-300 p-2 py-3 flex flex-col gap-4 w-full"
  >
    <div v-for="(condition, i) in props.conditions" :key="condition.field">
      <AssignmentCondition
        :condition="condition"
        :doctype="'HD Ticket'"
        :isChild="props.isChild"
        :itemIndex="i"
        @remove="removeCondition(condition)"
        :level="props.level + 1"
      />
    </div>
    <span
      v-if="props.conditions.length == 0"
      class="flex h-5 items-center px-3 text-sm text-gray-600"
    >
      Empty - Add a condition
    </span>
    <div v-if="props.isChild" class="flex">
      <Dropdown
        v-slot="{ open }"
        :options="[
          {
            label: 'Add condition',
            onClick: () => {
              conditions.push({
                field: null,
                operator: 'equals',
                value: '',
                conjunction: 'and',
              });
            },
          },
          props.level < 3 && {
            label: 'Add condition group',
            onClick: () => {
              conditions.push({
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
                conjunction: 'and',
              });
            },
          },
        ]"
      >
        <Button variant="ghost">
          Add condition
          <template #prefix>
            <FeatherIcon :name="'plus'" class="h-4" />
          </template>
          <template #suffix>
            <FeatherIcon
              :name="open ? 'chevron-up' : 'chevron-down'"
              class="h-4"
            />
          </template>
        </Button>
      </Dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
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

function removeCondition(condition) {
  props.conditions.splice(props.conditions.indexOf(condition), 1);
}
</script>
