<template>
  <div
    class="grid gap-2 px-2 items-center"
    :style="{
      gridTemplateColumns: getGridTemplateColumnsForTable(props.columns),
    }"
  >
    <div
      v-for="column in props.columns"
      :key="column.key"
      class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
    >
      <div v-if="column.key === 'default_priority'">
        <Checkbox
          v-model="props.row.default_priority"
          @update:modelValue="(e) => onDefaultPriorityChange(e)"
        />
      </div>
      <div
        v-else-if="
          column.key === 'response_time' || column.key === 'resolution_time'
        "
      >
        <Popover>
          <template #target="{ togglePopover }">
            <div
              @click="togglePopover()"
              class="min-h-7 w-full cursor-pointer select-none leading-5 p-1 px-2 hover:bg-gray-200 rounded"
            >
              {{ formatTimeHMS(props.row[column.key]) }}
            </div>
          </template>
          <template #body>
            <div class="absolute bg-white top-2">
              <DurationPicker v-model="props.row[column.key]" />
            </div>
          </template>
        </Popover>
      </div>
      <div v-else>
        <Select
          class="w-full bg-transparent cursor-pointer border-0 focus-visible:!ring-0 bg-none"
          :options="priorityOptions"
          v-model="props.row[column.key]"
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
  <hr class="my-0.5" v-if="!props.isLast" />
  <EditResponseResolutionModal v-model="dialog" :row="props.row" />
</template>

<script setup lang="ts">
import DurationPicker from "@/components/frappe-ui/DurationPicker.vue";
import { slaData } from "@/stores/sla";
import { getGridTemplateColumnsForTable, TemplateOption } from "@/utils";
import { Button, Checkbox, Dropdown, Popover, Select } from "frappe-ui";
import { inject, ref } from "vue";
import EditResponseResolutionModal from "./Modals/EditResponseResolutionModal.vue";
import { formatTimeHMS } from "./utils";

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
});

const isConfirmingDelete = ref(false);
const dialog = ref(false);
const priorityData = ref({
  priority: props.row.priority,
  resolution_time: props.row.resolution_time,
  response_time: props.row.response_time,
  default_priority: props.row.default_priority,
});

const priorityOptions = inject<Array<any>>("priorityOptions");

const dropdownOptions = [
  {
    label: "Edit",
    onClick: () => editItem(),
    icon: "edit",
  },
  {
    label: "Delete",
    component: (props) =>
      TemplateOption({
        option: "Delete",
        icon: "trash-2",
        active: props.active,
        variant: "gray",
        onClick: (event) => deleteItem(event),
      }),
    condition: () => !isConfirmingDelete.value,
  },
  {
    label: "Confirm Delete",
    component: (props) =>
      TemplateOption({
        option: "Confirm Delete",
        icon: "trash-2",
        active: props.active,
        variant: "danger",
        onClick: (event) => deleteItem(event),
      }),
    condition: () => isConfirmingDelete.value,
  },
];

const deleteItem = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  slaData.value.priorities.splice(
    slaData.value.priorities.indexOf(props.row),
    1
  );
};

const editItem = () => {
  dialog.value = true;
  priorityData.value = {
    priority: props.row.priority,
    resolution_time: props.row.resolution_time,
    response_time: props.row.response_time,
    default_priority: props.row.default_priority,
  };
};

const onDefaultPriorityChange = (defaultPriority) => {
  slaData.value.priorities.forEach((priority) => {
    priority.default_priority = false;
  });
  props.row.default_priority = defaultPriority;
};
</script>
