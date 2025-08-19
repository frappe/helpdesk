<template>
  <div
    class="grid gap-2 py-3.5 px-4 items-center"
    :style="{
      gridTemplateColumns: getGridTemplateColumnsForTable(props.columns),
    }"
  >
    <div
      v-for="column in props.columns"
      :key="column.key"
      class="w-full overflow-hidden whitespace-nowrap text-ellipsis"
    >
      <div v-if="column.key === 'status'">
        <Select
          class="w-[160px] bg-transparent cursor-pointer border-0 focus-visible:!ring-0 bg-none"
          :options="statusOptions"
          v-model="props.row['status']"
        />
      </div>
      <div v-else-if="column.key === 'sla_behavior'">
        <Select
          class="w-[160px] bg-transparent cursor-pointer border-0 focus-visible:!ring-0 bg-none"
          :options="slaBehaviorOptions"
          v-model="props.row['sla_behavior']"
        />
      </div>
    </div>
    <div class="flex justify-end">
      <Dropdown placement="right" :options="dropdownOptions">
        <Button
          icon="more-horizontal"
          variant="ghost"
          @click="isConfirmingDelete = false"
        />
      </Dropdown>
    </div>
  </div>
  <hr v-if="!props.isLast" />
  <Dialog
    v-model="dialog"
    @after-leave="isConfirmingDelete = false"
    :options="{
      title: 'Edit Status',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Status"
          label="Status"
          v-model="statusData.status"
          :options="statusOptions"
          required
        />
        <FormControl
          :type="'select'"
          size="sm"
          variant="subtle"
          placeholder="Select Status"
          label="SLA behavior"
          v-model="statusData.sla_behavior"
          :options="slaBehaviorOptions"
          required
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-between">
        <div>
          <Button
            variant="subtle"
            :theme="isConfirmingDelete ? 'red' : 'gray'"
            :label="isConfirmingDelete ? 'Confirm Delete' : 'Delete'"
            @click="deleteItem"
            icon-left="trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog = false"
            label="Cancel"
          />
          <Button variant="solid" @click="onSave" label="Save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Button, Select, Dialog, toast } from "frappe-ui";
import { ConfirmDelete, getGridTemplateColumnsForTable } from "@/utils";

const props = defineProps({
  columns: {
    type: Array<any>,
    required: true,
  },
  row: {
    type: Object,
    required: true,
  },
  isLast: {
    type: Boolean,
    default: false,
  },
  statusList: {
    type: Array<any>,
    required: true,
  },
});

const dialog = ref(false);
const isConfirmingDelete = ref(false);
const statusData = ref({
  status: props.row.status,
  sla_behavior: props.row.sla_behavior,
});

const statusOptions = [
  {
    label: "Open",
    value: "Open",
  },
  {
    label: "Replied",
    value: "Replied",
  },
  {
    label: "Resolved",
    value: "Resolved",
  },
  {
    label: "Closed",
    value: "Closed",
  },
];

const slaBehaviorOptions = [
  {
    label: "Fulfilled",
    value: "Fulfilled",
  },
  {
    label: "Paused",
    value: "Paused",
  },
];

const dropdownOptions = [
  {
    label: "Edit",
    onClick: () => editItem(),
    icon: "edit",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteItem(),
    isConfirmingDelete,
  }),
];

const deleteItem = () => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  props.statusList.splice(props.statusList.indexOf(props.row), 1);
};

const editItem = () => {
  statusData.value = {
    status: props.row.status,
    sla_behavior: props.row.sla_behavior,
  };
  dialog.value = true;
};

function onSave() {
  if (!statusData.value.status) {
    toast.error("Please select a status");
    return;
  }

  if (!statusData.value.sla_behavior) {
    toast.error("Please select an SLA behavior");
    return;
  }

  const isDuplicate = props.statusList.some(
    (item) => item.status === statusData.value.status && item !== props.row
  );

  if (isDuplicate) {
    toast.error("A status with this name already exists");
    return;
  }

  props.row.status = statusData.value.status;
  props.row.sla_behavior = statusData.value.sla_behavior;

  statusData.value = {
    status: "",
    sla_behavior: "",
  };

  dialog.value = false;
}
</script>
