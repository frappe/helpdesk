<template>
  <Dialog
    v-model:open="dialog.show"
    @after-leave="resetForm"
    :title="dialog.isEditing ? __('Edit workday') : __('Add workday')"
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            :type="'select'"
            size="sm"
            variant="subtle"
            :placeholder="__('Select workday')"
            :label="__('Workday')"
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
            :label="__('Start time')"
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
            :label="__('End time')"
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
            :label="isConfirmingDelete ? __('Confirm Delete') : __('Delete')"
            @click="deleteWorkDay"
            icon-left="lucide-trash-2"
          />
        </div>
        <div class="flex gap-2">
          <Button
            variant="subtle"
            theme="gray"
            @click="dialog.show = false"
            :label="__('Cancel')"
          />
          <Button variant="solid" @click="onSave" :label="__('Save')" />
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
import type { HDServiceDay } from "@/types/doctypes";

type WorkDayRow = Partial<
  Pick<
    HDServiceDay,
    "workday" | "start_time" | "end_time" | "break_start" | "break_end"
  >
>;

const TIME_FIELDS = ["start_time", "end_time", "break_start", "break_end"] as const;

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

function onSave() {
  if (!validateForm()) {
    toast.error(__("Please fix the errors in the form"));
    return;
  }
  try {
    const saved = dialog.value.isEditing ? updateRow() : addRow();
    if (!saved) return;
    if (applyToAll.value) applyBreakToOtherDays(getRow());
    dialog.value.show = false;
  } catch (error) {
    toast.error(__("Failed to save workday: {0}", [String(error)]));
  }
}

function validateForm() {
  const isWorkdayValid = validateField("workday");
  const isStartTimeValid = validateField("start_time");
  const isEndTimeValid = validateField("end_time") && validateTimeRange();
  return (
    isWorkdayValid && isStartTimeValid && isEndTimeValid && validateBreak()
  );
}

function validateField(field: keyof typeof errors & keyof typeof workDayData) {
  errors[field] = workDayData[field] ? "" : __("This field is required");
  return !errors[field];
}

function validateTimeRange() {
  if (!workDayData.start_time || !workDayData.end_time) {
    if (!workDayData.start_time) errors.start_time = __("Start time is required");
    if (!workDayData.end_time) errors.end_time = __("End time is required");
    return false;
  }
  if (toMinutes(workDayData.start_time) >= toMinutes(workDayData.end_time)) {
    errors.end_time = __("End time must be after start time");
    return false;
  }
  errors.end_time = "";
  return true;
}

function validateBreak() {
  errors.break = getBreakError(workDayData);
  return !errors.break;
}

/** Replace the edited row in the list; false when it is no longer there. */
function updateRow() {
  const index = props.workDaysList.findIndex(
    (item) => item.workday === dialog.value.data?.workday
  );
  if (index === -1) return false;
  const row = props.workDaysList[index];
  props.workDaysList.splice(index, 1, { ...row, ...getRow(row) });
  if (!applyToAll.value) toast.success(__("Workday updated successfully."));
  return true;
}

/** Append the form as a new row; false when that workday already exists. */
function addRow() {
  if (props.workDaysList.some((item) => item.workday === workDayData.workday)) {
    errors.workday = __("This workday already exists");
    toast.error(__("A workday with this name already exists"));
    return false;
  }
  props.workDaysList.push(getRow());
  if (!applyToAll.value) toast.success(__("Workday added successfully."));
  return true;
}

/**
 * The form as a row, times as HH:MM:SS. A time equal to the loaded one keeps
 * its loaded form (e.g. "9:00:00", or null for no break), so an unchanged save
 * changes nothing.
 */
function getRow(loaded: WorkDayRow = {}): WorkDayRow {
  const row: WorkDayRow = { workday: workDayData.workday };
  for (const field of TIME_FIELDS) {
    const time = formatTimeToHHMMSS(workDayData[field]);
    row[field] = time === formatTimeToHHMMSS(loaded[field]) ? loaded[field] : time;
  }
  return row;
}

/** Copy the break to every other workday whose hours contain it, then toast. */
function applyBreakToOtherDays(row: WorkDayRow) {
  const skipped: string[] = [];
  let applied = 1;
  for (const day of props.workDaysList) {
    if (day.workday === row.workday) continue;
    const withBreak = { ...day, break_start: row.break_start, break_end: row.break_end };
    if (getBreakError(withBreak)) {
      skipped.push(day.workday);
      continue;
    }
    Object.assign(day, withBreak);
    applied++;
  }
  toastAppliedBreak(applied, skipped);
}

function toastAppliedBreak(applied: number, skipped: string[]) {
  const message =
    applied === 1
      ? __("Break applied to 1 workday.")
      : __("Break applied to {0} workdays.", [String(applied)]);
  if (!skipped.length) return toast.success(message);
  const skippedMessage = __("Skipped {0}: outside working hours.", [skipped.join(", ")]);
  toast.warning(`${message} ${skippedMessage}`);
}

function deleteWorkDay(event: Event) {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  const index = props.workDaysList.findIndex(
    (item) => item.workday === dialog.value.data?.workday
  );
  if (index !== -1) props.workDaysList.splice(index, 1);
  dialog.value.show = false;
}

function loadForm(data: WorkDayRow) {
  workDayData.workday = data.workday || "";
  for (const field of TIME_FIELDS) {
    workDayData[field] = formatTimeToHHMMSS(data[field]);
  }
}

function resetForm() {
  loadForm({});
  Object.assign(errors, { workday: "", start_time: "", end_time: "", break: "" });
  applyBreakToAll.value = false;
  isConfirmingDelete.value = false;
}

function formatTimeToHHMMSS(time?: string | null) {
  const parts = (time || "").split(":");
  if (parts.length < 2 || parts.length > 3 || !parts.every((part) => /^\d{1,2}$/.test(part))) {
    return "";
  }
  const [hours, minutes, seconds = "00"] = parts;
  return [hours, minutes, seconds].map((part) => part.padStart(2, "0")).join(":");
}

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
    if (!isOpen) return;
    if (dialog.value.isEditing && dialog.value.data) loadForm(dialog.value.data);
    else resetForm();
  }
);
</script>
