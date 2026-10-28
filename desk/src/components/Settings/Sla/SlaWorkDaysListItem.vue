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
      <div
        v-if="column.key === 'start_time' || column.key === 'end_time'"
        class="whitespace-normal"
      >
        {{ formatTime(props.row[column.key]) }}
      </div>
      <div
        v-else-if="column.key === 'break'"
        class="flex flex-wrap gap-x-1 whitespace-normal"
      >
        <template v-if="hasBreak">
          <span class="whitespace-nowrap">
            {{ formatTime(props.row.break_start) }}
          </span>
          <span class="whitespace-nowrap">
            – {{ formatTime(props.row.break_end) }}
          </span>
        </template>
        <span v-else class="text-ink-gray-4">—</span>
      </div>
      <div v-else class="ms-2">
        <select
          class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-5 p-0 ps-2 pe-5 bg-transparent -ms-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
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
      <Dropdown
        align="end"
        :options="dropdownOptions"
        @update:open="(open) => open && (isConfirmingDelete = false)"
      >
        <Button icon="lucide-more-horizontal" variant="ghost" />
      </Dropdown>
    </div>
    <div
      v-if="hasBreak && !hasBreakColumn"
      class="col-span-full -mt-1 text-ink-gray-5"
    >
      {{ __("Break") }} {{ formatTime(props.row.break_start) }} –
      {{ formatTime(props.row.break_end) }}
    </div>
  </div>
  <hr v-if="!props.isLast" />
  <WorkDayModal
    v-model="dialog"
    :workDaysList="slaData.support_and_resolution"
  />
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Button, Dropdown } from "frappe-ui";
import WorkDayModal from "./Modals/WorkDayModal.vue";
import { ConfirmDelete, getGridTemplateColumnsForTable } from "@/utils";
import { slaData } from "@/stores/sla";
import { __ } from "@/translation";

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
  break_start?: string | null;
  break_end?: string | null;
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
const hasBreak = computed(() =>
  Boolean(props.row.break_start && props.row.break_end)
);
const hasBreakColumn = computed(() =>
  props.columns.some((column) => column.key === "break")
);

const dropdownOptions = [
  {
    label: "Edit",
    onClick: () => editWorkDay(),
    icon: "lucide-edit",
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
    break_start: props.row.break_start,
    break_end: props.row.break_end,
  };
};

const formatTime = (time) => {
  if (!time) return "00:00";
  const [hours, minutes] = time.split(":");
  const date = new Date();
  date.setHours(parseInt(hours) || 0, parseInt(minutes) || 0, 0);

  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
};
</script>
