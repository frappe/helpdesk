<template>
  <Dialog
    v-model="dialog.show"
    :options="{
      size: 'sm',
      title: dialog.editing ? 'Edit Holiday' : 'Add Holiday',
    }"
    @after-leave="resetForm"
  >
    <template #body-content>
      <div class="flex flex-col gap-4 mt-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Date" required />
          <DatePicker
            :value="dayjs(dialog.holiday_date).format('MM-DD-YYYY')"
            @update:model-value="dialog.holiday_date = $event"
            :formatter="(date) => getFormattedDate(date)"
            variant="subtle"
            placeholder="Date"
            class="w-full"
            id="holiday_date"
            required
            @change="errors.holiday_date = ''"
          />
          <ErrorMessage :message="errors.holiday_date" />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormControl
            :type="'textarea'"
            size="sm"
            variant="subtle"
            placeholder="National holiday, etc."
            label="Description"
            v-model="dialog.description"
            required
            @change="errors.description = ''"
          />
          <ErrorMessage :message="errors.description" />
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="subtle"
          theme="gray"
          label="Cancel"
          @click="dialog.show = false"
        />
        <Button
          variant="solid"
          icon-left="plus"
          label="Add Holiday"
          @click="onSave"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { getFormattedDate } from "@/utils";
import {
  Dialog,
  FormControl,
  Button,
  FormLabel,
  toast,
  ErrorMessage,
  DatePicker,
} from "frappe-ui";
import { ref } from "vue";
import dayjs from "dayjs";
import { holidayData } from "@/stores/holidayList";

interface ModelType {
  show: boolean;
  holiday_date: null | string | Date;
  description: string;
  editing: null | any;
}

const dialog = defineModel<ModelType>();

const errors = ref({
  holiday_date: "",
  description: "",
});

const resetForm = () => {
  dialog.value.holiday_date = new Date();
  dialog.value.description = "";
  errors.value = {
    holiday_date: "",
    description: "",
  };
};

const onSave = () => {
  if (dialog.value.description?.trim() === "") {
    errors.value.description = "Please enter a description";
  }
  if (!dialog.value.holiday_date) {
    errors.value.holiday_date = "Please enter a valid date";
  }

  if (errors.value.holiday_date || errors.value.description) {
    return;
  }

  const holidayDate = dayjs(dialog.value.holiday_date).startOf("day");
  const fromDate = dayjs(holidayData.value.from_date).startOf("day");
  const toDate = dayjs(holidayData.value.to_date).startOf("day");

  if (holidayDate.isBefore(fromDate) || holidayDate.isAfter(toDate)) {
    toast.error(
      `Holiday date must be between ${getFormattedDate(
        holidayData.value.from_date
      )} and ${getFormattedDate(holidayData.value.to_date)}`
    );
    return;
  }

  if (dialog.value.editing) {
    const holidayExists = holidayData.value.holidays.find(
      (h) =>
        getFormattedDate(h.holiday_date) ===
        getFormattedDate(dialog.value.holiday_date)
    );

    // If the holiday exists and user is trying to add a new holiday on the same date, show error
    if (
      holidayExists &&
      getFormattedDate(holidayExists.holiday_date) !==
        getFormattedDate(dialog.value.editing.holiday_date)
    ) {
      toast.error("Holiday already exists");
      return;
    }
    const holidayIndex = holidayData.value.holidays.indexOf(
      dialog.value.editing
    );
    holidayData.value.holidays.splice(holidayIndex, 1, {
      ...dialog.value,
      weekly_off: 0,
    });
  } else {
    const index = holidayData.value.holidays.findIndex(
      (h) =>
        getFormattedDate(h.holiday_date) ===
        getFormattedDate(dialog.value.holiday_date)
    );
    if (index !== -1) {
      toast.error("Holiday already exists");
      return;
    }
    holidayData.value.holidays.push({
      ...dialog.value,
      weekly_off: 0,
    });
  }

  dialog.value = {
    show: false,
    holiday_date: null,
    description: "",
    editing: null,
  };
};
</script>
