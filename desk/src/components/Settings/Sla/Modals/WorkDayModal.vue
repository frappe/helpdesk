<template>
  <Dialog
    v-model="dialog.show"
    @after-leave="resetForm"
    :options="{
      title: dialog.isEditing ? __('Edit workday') : __('Add workday'),
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <FormControl
            :type="'select'"
            size="sm"
            variant="subtle"
            :placeholder="__('Select Workday')"
            :label="__('Workday')"
            v-model="workDayData.workday"
            :options="[
              {
                label: __('Monday'),
                value: 'Monday',
              },
              {
                label: __('Tuesday'),
                value: 'Tuesday',
              },
              {
                label: __('Wednesday'),
                value: 'Wednesday',
              },
              {
                label: __('Thursday'),
                value: 'Thursday',
              },
              {
                label: __('Friday'),
                value: 'Friday',
              },
              {
                label: __('Saturday'),
                value: 'Saturday',
              },
              {
                label: __('Sunday'),
                value: 'Sunday',
              },
            ]"
            :class="{ 'border-red-500': errors.workday }"
            @blur="validateField('workday')"
          />
          <ErrorMessage :message="errors.workday" class="mt-2" />
        </div>

        <div>
          <FormControl
            :type="'time'"
            size="sm"
            variant="subtle"
            :placeholder="__('Start Time')"
            :label="__('Start Time')"
            v-model="workDayData.start_time"
            :class="{ 'border-red-500': errors.start_time }"
            @blur="validateField('start_time')"
          />
          <ErrorMessage :message="errors.start_time" class="mt-2" />
        </div>

        <div>
          <FormControl
            :type="'time'"
            size="sm"
            variant="subtle"
            :placeholder="__('End Time')"
            :label="__('End Time')"
            v-model="workDayData.end_time"
            :class="{ 'border-red-500': errors.end_time }"
            @blur="validateTimeRange"
          />
          <ErrorMessage :message="errors.end_time" class="mt-2" />
        </div>
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
            icon-left="trash-2"
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
import { ref, defineModel, reactive, watch } from "vue";
import { Dialog, FormControl, Button, toast } from "frappe-ui";
import { __ } from "@/translation";

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
});

const errors = reactive({
  workday: "",
  start_time: "",
  end_time: "",
});

const deleteWorkDay = (event) => {
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  const item = props.workDaysList.findIndex(
    (item) => item.workday === workDayData.workday,
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
      "0",
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
  errors.workday = "";
  errors.start_time = "";
  errors.end_time = "";
  isConfirmingDelete.value = false;
}

const validateField = (field: string) => {
  if (!workDayData[field as keyof typeof workDayData]) {
    errors[field as keyof typeof errors] = __("This field is required");
    return false;
  }
  errors[field as keyof typeof errors] = "";
  return true;
};

const validateTimeRange = () => {
  if (!workDayData.start_time || !workDayData.end_time) {
    if (!workDayData.start_time)
      errors.start_time = __("Start time is required");
    if (!workDayData.end_time) errors.end_time = __("End time is required");
    return false;
  }

  const [startHours, startMinutes] = workDayData.start_time
    .split(":")
    .map(Number);
  const [endHours, endMinutes] = workDayData.end_time.split(":").map(Number);

  if (
    endHours < startHours ||
    (endHours === startHours && endMinutes <= startMinutes)
  ) {
    errors.end_time = __("End time must be after start time");
    return false;
  }

  errors.end_time = "";
  return true;
};

const validateForm = () => {
  const isWorkdayValid = validateField("workday");
  const isStartTimeValid = validateField("start_time");
  const isEndTimeValid = validateField("end_time") && validateTimeRange();

  return isWorkdayValid && isStartTimeValid && isEndTimeValid;
};

const onSave = () => {
  if (!validateForm()) {
    toast.error(__("Please fix the errors in the form"));
    return;
  }

  try {
    if (dialog.value.isEditing) {
      const itemIndex = props.workDaysList.findIndex(
        (item) => item.workday === dialog.value.data?.workday,
      );
      if (itemIndex !== -1) {
        const updatedItem = {
          ...props.workDaysList[itemIndex],
          ...workDayData,
        };
        props.workDaysList.splice(itemIndex, 1, updatedItem);
        toast.success(__("Workday updated"));
      }
    } else {
      const isDuplicate = props.workDaysList.some(
        (item) => item.workday === workDayData.workday,
      );

      if (isDuplicate) {
        errors.workday = __("This workday already exists");
        toast.error(__("A workday with this name already exists"));
        return;
      }

      const newWorkDay = { ...workDayData };
      props.workDaysList.push(newWorkDay);
      toast.success(__("Workday added"));
    }
    dialog.value.show = false;
  } catch (error) {
    toast.error(__("Failed to save workday: {0}", [error]));
  }
};

watch(
  () => dialog.value.show,
  (isOpen) => {
    if (isOpen) {
      if (dialog.value.isEditing && dialog.value.data) {
        workDayData.workday = dialog.value.data.workday;
        workDayData.start_time = formatTimeToHHMMSS(
          dialog.value.data.start_time,
        );
        workDayData.end_time = formatTimeToHHMMSS(dialog.value.data.end_time);
      } else {
        resetForm();
      }
    }
  },
);
</script>
