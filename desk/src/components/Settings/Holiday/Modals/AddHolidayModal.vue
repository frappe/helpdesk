<template>
  <Dialog
    v-model="dialog.show"
    :options="{
      size: 'sm',
      title: dialog.isEditing ? 'Edit Holiday' : 'Add Holiday',
    }"
    @after-leave="resetForm"
  >
    <template #body-content>
      <div class="flex flex-col gap-4 mt-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Date" required />
          <DatePicker
            v-model="dialog.holiday_date"
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
} from "frappe-ui";
import DatePicker from "frappe-ui/src/components/DatePicker/DatePicker.vue";
import { ref } from "vue";
import dayjs from "dayjs";
import { holidayData } from "@/stores/holidayList";

interface ModelType {
  show: boolean;
  holiday_date: null | string;
  description: string;
  isEditing: boolean;
}

const dialog = defineModel<ModelType>();

const errors = ref({
  holiday_date: "",
  description: "",
});

const resetForm = () => {
  dialog.value.holiday_date = null;
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

  const index = holidayData.value.holidays.findIndex(
    (h) =>
      getFormattedDate(h.holiday_date) ===
      getFormattedDate(dialog.value.holiday_date)
  );

  if (index !== -1 && !dialog.value.isEditing) {
    toast.error("Holiday already exists");
    return;
  }

  if (index === -1 && !dialog.value.isEditing) {
    holidayData.value.holidays.push({
      ...dialog.value,
      weekly_off: 0,
    });
  } else {
    holidayData.value.holidays.splice(index, 1, {
      ...dialog.value,
      weekly_off: 0,
    });
  }

  dialog.value = {
    show: false,
    holiday_date: null,
    description: "",
    isEditing: false,
  };
};
</script>
