<template>
  <div class="rounded-md border px-2 border-gray-300 text-sm">
    <div
      class="grid p-2 px-4 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumnsForTable(columns),
      }"
      v-if="statusList?.length !== 0"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis ml-2"
      >
        {{ column.label }}
        <span v-if="column.isRequired" class="text-red-500">*</span>
      </div>
    </div>
    <hr v-if="statusList?.length !== 0" />
    <SlaStatusListItem
      v-for="(row, index) in statusList"
      :key="index + row.status + row.id"
      :row="row"
      :columns="columns"
      :isLast="index === statusList.length - 1"
      :statusList="statusList"
    />
    <div v-if="statusList?.length === 0" class="text-center p-4 text-gray-600">
      No status in the list
    </div>
  </div>
  <div
    class="flex items-center justify-between mt-2.5"
    v-if="
      slaData.statuses.length < 4 ||
      slaDataErrors.statuses ||
      slaDataErrors.statuses_conflict
    "
  >
    <div>
      <Button
        v-if="slaData.statuses.length < 4"
        variant="subtle"
        label="Add row"
        @click="addRow"
        icon-left="plus"
      />
    </div>
    <ErrorMessage
      :message="slaDataErrors.statuses || slaDataErrors.statuses_conflict"
    />
  </div>
</template>

<script setup lang="ts">
import { Button, toast } from "frappe-ui";
import SlaStatusListItem from "./SlaStatusListItem.vue";
import { slaData, slaDataErrors, validateSlaData } from "@/stores/sla";
import { watchDebounced } from "@vueuse/core";
import { getGridTemplateColumnsForTable } from "@/utils";

const props = defineProps({
  statusList: {
    type: Array<any>,
    required: true,
  },
});

const statusOptions = ["Open", "Resolved", "Closed", "Replied"];

const addRow = () => {
  const existingStatuses = props.statusList.map((s) => s?.status);

  const availableStatuses = statusOptions.filter(
    (status) => !existingStatuses.includes(status)
  );

  if (availableStatuses.length === 0) {
    toast.error("All available statuses have already been added");
    return;
  }

  const newStatus = availableStatuses[0];

  if (!newStatus) {
    toast.error("No valid status available to add");
    return;
  }

  const newStatusItem = {
    status: newStatus,
    sla_behavior: "Fulfilled",
    id: Math.random().toString(36).substring(2, 9),
  };

  props.statusList.push(newStatusItem);
};

const columns = [
  {
    label: "When Status is",
    key: "status",
    isRequired: true,
  },
  {
    label: "SLA is",
    key: "sla_behavior",
    isRequired: true,
  },
];

watchDebounced(
  () => [...props.statusList],
  () => {
    validateSlaData("statuses");
  },
  { deep: true, debounce: 300 }
);
</script>
