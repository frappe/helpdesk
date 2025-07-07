<template>
  <Dialog
    v-model="dialog"
    :options="{ size: 'sm', title: 'Add new holiday' }"
    @after-leave="resetForm"
  >
    <template #body-content>
      <div class="flex flex-col gap-4 mt-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Date" required />
          <DatePicker
            v-model="newHolidayData.holiday_date"
            :formatter="(date) => getFormattedDate(date)"
            variant="subtle"
            placeholder="Date"
            class="w-full"
            id="holiday_date"
            required
            @change="errors.holiday_date = ''"
          />
          <div v-if="errors.holiday_date" class="text-red-500 text-xs mt-1">
            {{ errors.holiday_date }}
          </div>
        </div>
        <div class="flex flex-col gap-1.5">
          <FormControl
            :type="'textarea'"
            size="sm"
            variant="subtle"
            placeholder="National holiday, etc."
            label="Description"
            v-model="newHolidayData.description"
            required
            @change="errors.description = ''"
          />
          <div v-if="errors.description" class="text-red-500 text-xs mt-1">
            {{ errors.description }}
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="subtle"
          theme="gray"
          label="Cancel"
          @click="dialog = false"
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
import { Dialog, FormControl, Button, FormLabel, toast } from "frappe-ui";
import DatePicker from "frappe-ui/src/components/DatePicker/DatePicker.vue";
import { ref } from "vue";
import dayjs from "dayjs";
import { holidayData } from "@/stores/holidayList";

const dialog = defineModel<boolean>();

const errors = ref({
  holiday_date: "",
  description: "",
});

const newHolidayData = ref({
  holiday_date: null,
  description: "",
});

const resetForm = () => {
  newHolidayData.value = {
    holiday_date: null,
    description: "",
  };
  errors.value = {
    holiday_date: "",
    description: "",
  };
};

const onSave = () => {
  if (newHolidayData.value.description?.trim() === "") {
    errors.value.description = "Please enter a description";
  }
  if (!newHolidayData.value.holiday_date) {
    errors.value.holiday_date = "Please enter a valid date";
  }

  if (errors.value.holiday_date || errors.value.description) {
    return;
  }

  const holidayDate = dayjs(newHolidayData.value.holiday_date).startOf("day");
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
      getFormattedDate(newHolidayData.value.holiday_date)
  );

  if (index !== -1) {
    toast.error("Holiday already exists");
    return;
  }
  holidayData.value.holidays.push({ ...newHolidayData.value, weekly_off: 0 });
  resetForm();
  dialog.value = false;
};
</script>
