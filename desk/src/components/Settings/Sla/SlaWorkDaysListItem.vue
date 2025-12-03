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
      <div v-if="column.key === 'start_time' || column.key === 'end_time'">
        {{ formatTime(props.row[column.key]) }}
      </div>
      <div v-else class="ml-2">
        <select
          class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 pl-2 pr-5 bg-transparent -ml-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
          v-model="props.row[column.key]"
        >
          <option
            v-for="option in workDayOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
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
  <WorkDayModal
    v-model="dialog"
    :workDaysList="slaData.support_and_resolution"
  />
</template>

<script setup lang="ts">
import { ref } from "vue";
<<<<<<< HEAD
import { Button, Select } from "frappe-ui";
=======
import { Button, Dropdown } from "frappe-ui";
>>>>>>> e2a2d29b (fix: bugs related to frappe-ui update)
import WorkDayModal from "./Modals/WorkDayModal.vue";
import { ConfirmDelete, getGridTemplateColumnsForTable } from "@/utils";
import { slaData } from "@/stores/sla";

interface Column {
  key: string;
  label: string;
  isRequired?: boolean;
}

interface WorkDay {
  id: string;
  workday: string;
  start_time: string;
  end_time: string;
}

const props = defineProps<{
  columns: Column[];
  row: WorkDay;
  isLast?: boolean;
}>();

const workDayOptions = [
  { label: "Monday", value: "Monday" },
  { label: "Tuesday", value: "Tuesday" },
  { label: "Wednesday", value: "Wednesday" },
  { label: "Thursday", value: "Thursday" },
  { label: "Friday", value: "Friday" },
  { label: "Saturday", value: "Saturday" },
  { label: "Sunday", value: "Sunday" },
];

const dialog = ref({
  show: false,
  isEditing: false,
  data: {},
});

const isConfirmingDelete = ref(false);

const dropdownOptions = [
  {
    label: "Edit",
    onClick: () => editWorkDay(),
    icon: "edit",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteWorkDay(),
    isConfirmingDelete,
  }),
];

const deleteWorkDay = () => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  const item = slaData.value.support_and_resolution.indexOf(props.row);
  if (item !== -1) {
    slaData.value.support_and_resolution.splice(item, 1);
  }
};

const editWorkDay = () => {
  dialog.value.show = true;
  dialog.value.isEditing = true;
  dialog.value.data = {
    workday: props.row.workday,
    start_time: props.row.start_time,
    end_time: props.row.end_time,
  };
};

const formatTime = (time) => {
  if (!time) return "00:00";
  const [hours, minutes] = time.split(":");
  const date = new Date();
  date.setHours(parseInt(hours) || 0, parseInt(minutes) || 0, 0);

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
};
</script>
