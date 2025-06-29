<template>
  <div class="rounded-md border p-1 border-gray-300 text-sm">
    <div
      class="grid p-2 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumnsForTable(columns),
      }"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
        <span v-if="column.isRequired" class="text-red-500">*</span>
      </div>
    </div>
    <hr class="my-0.5" />
    <SlaPriorityListItem
      v-for="(row, index) in props.priorityList"
      :key="row.name"
      :row="row"
      :columns="columns"
      :isLast="index === props.priorityList.length - 1"
      :priorityList="props.priorityList"
    />
    <div
      v-if="props.priorityList?.length === 0"
      class="text-center p-4 text-gray-600"
    >
      No items in the list
    </div>
  </div>
  <div class="flex items-center justify-between">
    <Button
      variant="subtle"
      label="Add row"
      class="mt-4"
      @click="addRow"
      icon-left="plus"
    />
    <div class="mt-2">
      <div v-if="slaDataErrors.default_priority" class="text-red-500 text-xs">
        {{ slaDataErrors.default_priority }}
      </div>
      <div v-if="slaDataErrors.priorities" class="text-red-500 text-xs">
        {{ slaDataErrors.priorities }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, toast } from "frappe-ui";
import SlaPriorityListItem from "./SlaPriorityListItem.vue";
import { computed } from "vue";
import { slaDataErrors, validateSlaData } from "./sla";
import { watchDebounced } from "@vueuse/core";
import { getGridTemplateColumnsForTable } from "@/utils";

const props = defineProps({
  priorityList: {
    type: Array<any>,
    required: true,
  },
  applySlaForResolution: {
    type: Boolean,
    required: true,
  },
});

const priorityOptions = ["Low", "Medium", "High", "Urgent"];

const addRow = () => {
  const existingPriorities = props.priorityList.map((p) => p.priority);
  const availablePriorities = priorityOptions.filter(
    (p) => !existingPriorities.includes(p)
  );

  if (availablePriorities.length === 0) {
    toast.error("All available priorities have already been added");
    return;
  }

  const newPriority = availablePriorities[0] || "Low";

  props.priorityList.push({
    priority: newPriority,
    resolution_time: 60 * 60,
    response_time: 60 * 60,
    default_priority: props.priorityList.length === 0,
  });
};

const columns = computed(() => [
  {
    label: "Priority",
    key: "priority",
    isRequired: true,
  },
  {
    label: "Default priority",
    key: "default_priority",
    isRequired: true,
  },
  {
    label: "First response time",
    key: "response_time",
    isRequired: true,
  },
  {
    label: "Resolution time",
    key: "resolution_time",
    isRequired: true,
  },
]);

watchDebounced(
  () => [...props.priorityList],
  () => {
    validateSlaData();
  },
  { deep: true, debounce: 300 }
);
</script>
