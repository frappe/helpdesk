<template>
  <Dialog
    v-model:open="dialog.show"
    @after-leave="resetForm"
    :title="dialog.isEditing ? 'Edit workday' : 'Add workday'"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            :type="'select'"
            size="sm"
            variant="subtle"
            placeholder="Select Workday"
            label="Workday"
            v-model="workDayData.workday"
            :options="[
              {
                label: 'Monday',
                value: 'Monday',
              },
              {
                label: 'Tuesday',
                value: 'Tuesday',
              },
              {
                label: 'Wednesday',
                value: 'Wednesday',
              },
              {
                label: 'Thursday',
                value: 'Thursday',
              },
              {
                label: 'Friday',
                value: 'Friday',
              },
              {
                label: 'Saturday',
                value: 'Saturday',
              },
              {
                label: 'Sunday',
                value: 'Sunday',
              },
            ]"
            :class="{ 'border-outline-red-4': errors.workday }"
            @blur="validateField('workday')"
          />
          <ErrorMessage :message="errors.workday" class="mt-2" />
        </div>

        <div>
          <FormControl
            :type="'time'"
            size="sm"
            variant="subtle"
            placeholder="Start Time"
            label="Start Time"
            v-model="workDayData.start_time"
            :class="{ 'border-outline-red-4': errors.start_time }"
            @change="validateField('start_time')"
          />
          <ErrorMessage :message="errors.start_time" class="mt-2" />
        </div>

        <div>
          <FormControl
            :type="'time'"
            size="sm"
            variant="subtle"
            placeholder="End Time"
            label="End Time"
            v-model="workDayData.end_time"
            :class="{ 'border-outline-red-4': errors.end_time }"
            @change="validateTimeRange"
          />
          <ErrorMessage :message="errors.end_time" class="mt-2" />
        </div>

        <div>
          <div class="grid grid-cols-2 gap-4">
            <FormControl
              type="time"
              size="sm"
              variant="subtle"
              :label="__('Break start')"
              v-model="workDayData.break_start"
            />
            <FormControl
              type="time"
              size="sm"
              variant="subtle"
              :label="__('Break end')"
              v-model="workDayData.break_end"
              @change="validateBreak"
            />
          </div>
          <ErrorMessage :message="errors.break" class="mt-2" />
        </div>

        <!-- invisible, not v-if: a layout shift on blur would swallow the Save click -->
        <Checkbox
          :class="{ invisible: !hasBreak }"
          v-model="applyBreakToAll"
          :label="__('Apply break to all workdays')"
        />
      </div>
    </template>
    <template #actions>
      <div
        class="flex"
        :class="{
          'justify-between': dialog.isEditing,
          'justify-end': !dialog.isEditing,
        }"
      >
        <div v-if="dialog.isEditing">
          <Button
            variant="subtle"
            :theme="isConfirmingDelete ? 'red' : 'gray'"
            :label="isConfirmingDelete ? 'Confirm Delete' : 'Delete'"
            @click="deleteWorkDay"
            icon-left="lucide-trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog.show = false"
            label="Cancel"
          />
          <Button variant="solid" @click="onSave" label="Save" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from "vue";
import { Dialog, FormControl, Button, Checkbox, toast } from "frappe-ui";
import { __ } from "@/translation";
import { getBreakError, toMinutes } from "@/stores/sla";

const isConfirmingDelete = ref(false);
const props = defineProps({
  workDaysList: {
    type: Array<any>,
    required: true,
  },
});

interface DialogData {
  show: boolean;
  isEditing: boolean;
  data?: any;
}

const dialog = defineModel<DialogData>({
  required: true,
  default: () => ({
    show: false,
    isEditing: false,
    data: {
      workday: "",
      start_time: "",
      end_time: "",
    },
  }),
});

const workDayData = reactive({
  workday: "",
  start_time: "",
  end_time: "",
  break_start: "",
  break_end: "",
});

const errors = reactive({
  workday: "",
  start_time: "",
  end_time: "",
  break: "",
});

const applyBreakToAll = ref(false);
const hasBreak = computed(() =>
  Boolean(workDayData.break_start && workDayData.break_end)
);
const applyToAll = computed(() => applyBreakToAll.value && hasBreak.value);

const deleteWorkDay = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  const item = props.workDaysList.findIndex(
    (item) => item.workday === workDayData.workday
  );
  if (item !== -1) {
    props.workDaysList.splice(item, 1);
  }
};

function formatTimeToHHMMSS(timeStr: string) {
  if (!timeStr) return "";

  if (/^\d{1,2}:\d{2}:\d{2}$/.test(timeStr)) {
    const [hours, minutes, seconds] = timeStr.split(":");
    return `${hours.padStart(2, "0")}:${minutes.padStart(
      2,
      "0"
    )}:${seconds.padStart(2, "0")}`;
  }

  if (/^\d{1,2}:\d{2}$/.test(timeStr)) {
    const [hours, minutes] = timeStr.split(":");
    return `${hours.padStart(2, "0")}:${minutes.padStart(2, "0")}:00`;
  }

  return "";
}

function resetForm() {
  workDayData.workday = "";
  workDayData.start_time = "";
  workDayData.end_time = "";
  workDayData.break_start = "";
  workDayData.break_end = "";
  errors.workday = "";
  errors.start_time = "";
  errors.end_time = "";
  errors.break = "";
  applyBreakToAll.value = false;
  isConfirmingDelete.value = false;
}

const validateField = (field: string) => {
  if (!workDayData[field as keyof typeof workDayData]) {
    errors[field as keyof typeof errors] = "This field is required";
    return false;
  }
  errors[field as keyof typeof errors] = "";
  return true;
};

const validateTimeRange = () => {
  if (!workDayData.start_time || !workDayData.end_time) {
    if (!workDayData.start_time) errors.start_time = "Start time is required";
    if (!workDayData.end_time) errors.end_time = "End time is required";
    return false;
  }

  if (toMinutes(workDayData.start_time) >= toMinutes(workDayData.end_time)) {
    errors.end_time = "End time must be after start time";
    return false;
  }

  errors.end_time = "";
  return true;
};

const validateForm = () => {
  const isWorkdayValid = validateField("workday");
  const isStartTimeValid = validateField("start_time");
  const isEndTimeValid = validateField("end_time") && validateTimeRange();

  return (
    isWorkdayValid && isStartTimeValid && isEndTimeValid && validateBreak()
  );
};

const validateBreak = () => {
  errors.break = getBreakError(workDayData);
  return !errors.break;
};

/** The form as a row, with break times as HH:MM:SS or empty. */
function getRow() {
  return {
    ...workDayData,
    break_start: formatTimeToHHMMSS(workDayData.break_start),
    break_end: formatTimeToHHMMSS(workDayData.break_end),
  };
}

/** Copy the break to every other workday whose hours contain it, then toast. */
function applyBreakToOtherDays(row: ReturnType<typeof getRow>) {
  let applied = 1;
  const skipped: string[] = [];
  for (const day of props.workDaysList) {
    if (day.workday === row.workday) continue;
    const withBreak = {
      ...day,
      break_start: row.break_start,
      break_end: row.break_end,
    };
    if (getBreakError(withBreak)) {
      skipped.push(day.workday);
      continue;
    }
    Object.assign(day, withBreak);
    applied++;
  }
  const message = __("Break applied to {0} workdays.", [String(applied)]);
  if (!skipped.length) return toast.success(message);
  toast.warning(
    `${message} ${__("Skipped {0}: outside working hours.", [
      skipped.join(", "),
    ])}`
  );
}

const onSave = () => {
  if (!validateForm()) {
    toast.error(__("Please fix the errors in the form"));
    return;
  }

  try {
    if (dialog.value.isEditing) {
      const itemIndex = props.workDaysList.findIndex(
        (item) => item.workday === dialog.value.data?.workday
      );
      if (itemIndex !== -1) {
        const updatedItem = {
          ...props.workDaysList[itemIndex],
          ...getRow(),
        };
        props.workDaysList.splice(itemIndex, 1, updatedItem);
        if (!applyToAll.value) {
          toast.success(__("Workday updated successfully."));
        }
      }
    } else {
      const isDuplicate = props.workDaysList.some(
        (item) => item.workday === workDayData.workday
      );

      if (isDuplicate) {
        errors.workday = "This workday already exists";
        toast.error(__("A workday with this name already exists"));
        return;
      }

      props.workDaysList.push(getRow());
      if (!applyToAll.value) {
        toast.success(__("Workday added successfully."));
      }
    }
    if (applyToAll.value) {
      applyBreakToOtherDays(getRow());
    }
    dialog.value.show = false;
  } catch (error) {
    toast.error(__(`Failed to save workday: ${error}`));
  }
};

// Re-check a shown break error as the times change, so a fixed break clears it.
watch(
  () => [
    workDayData.start_time,
    workDayData.end_time,
    workDayData.break_start,
    workDayData.break_end,
  ],
  () => errors.break && validateBreak()
);

watch(
  () => dialog.value.show,
  (isOpen) => {
    if (isOpen) {
      if (dialog.value.isEditing && dialog.value.data) {
        workDayData.workday = dialog.value.data.workday;
        workDayData.start_time = formatTimeToHHMMSS(
          dialog.value.data.start_time
        );
        workDayData.end_time = formatTimeToHHMMSS(dialog.value.data.end_time);
        workDayData.break_start = formatTimeToHHMMSS(
          dialog.value.data.break_start
        );
        workDayData.break_end = formatTimeToHHMMSS(dialog.value.data.break_end);
      } else {
        resetForm();
      }
    }
  }
);
</script>
