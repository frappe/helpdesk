<template>
  <AssignmentConditions :conditions="props.conditions" :level="0" />
  <Dropdown
    class="mt-2"
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
      {
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
    <Button>
      Add condition
      <template #suffix>
        <FeatherIcon :name="open ? 'chevron-up' : 'chevron-down'" class="h-4" />
      </template>
    </Button>
  </Dropdown>
</template>

<script setup lang="ts">
import AssignmentConditions from "./AssignmentConditions/AssignmentConditions.vue";
import { Button, FeatherIcon, Dropdown } from "frappe-ui";
import { onMounted, reactive } from "vue";

const props = defineProps({
  conditions: {
    type: Array<Conditions>,
    required: true,
  },
});

type Conditions = {
  field: string | object | null;
  operator: string;
  value: string | number | boolean | Array<any>;
  conjunction?: string;
};

// let conditions = reactive<Array<Conditions>>([]);

// onMounted(() => {
//   if (props.conditions?.length > 0) {
//     conditions = props.conditions;
//   }
// });
</script>
