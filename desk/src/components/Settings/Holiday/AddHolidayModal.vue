<template>
  <Dialog v-model="dialog" :options="{ size: 'sm' }">
    <template #body-title>
      <h3 class="text-2xl font-semibold">Add new holiday</h3>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4 mt-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Date" required />
          <DatePicker
            v-model="holidayData.holiday_date"
            :formatter="(date) => getFormat(date)"
            variant="subtle"
            placeholder="Date"
            class="w-full"
            id="holiday_date"
            required
          />
        </div>
        <FormControl
          :type="'textarea'"
          size="sm"
          variant="subtle"
          placeholder="Description"
          label="Description"
          v-model="holidayData.description"
          required
        />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <div class="flex gap-2">
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
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { getFormat } from "@/utils";
import { Dialog, FormControl, Button, FormLabel, toast } from "frappe-ui";
import DatePicker from "frappe-ui/src/components/DatePicker/DatePicker.vue";
import { ref } from "vue";

const dialog = defineModel<boolean>();

const props = defineProps({
  holidays: {
    type: Array<any>,
    required: true,
  },
  from_date: {
    type: String,
    required: true,
  },
  to_date: {
    type: String,
    required: true,
  },
});

const holidayData = ref({
  holiday_date: null,
  description: "",
});

const onSave = () => {
  if (!holidayData.value.description) {
    toast.error("Please enter a description");
    return;
  }

  if (!holidayData.value.holiday_date) {
    toast.error("Please select a date for the holiday");
    return;
  }

  const holidayDate = new Date(holidayData.value.holiday_date);
  const fromDate = new Date(props.from_date);
  const toDate = new Date(props.to_date);

  // Set time to midnight for accurate date comparison
  holidayDate.setHours(0, 0, 0, 0);
  fromDate.setHours(0, 0, 0, 0);
  toDate.setHours(0, 0, 0, 0);

  if (holidayDate < fromDate || holidayDate > toDate) {
    toast.error(
      `Holiday date must be between ${props.from_date} and ${props.to_date}`
    );
    return;
  }

  const index = props.holidays.findIndex(
    (h) => h.holiday_date === holidayData.value.holiday_date
  );

  if (index !== -1) {
    toast.error("Holiday already exists");
    return;
  }
  props.holidays.push({ ...holidayData.value, weekly_off: 0 });

  holidayData.value = {
    holiday_date: null,
    description: "",
  };
  dialog.value = false;
};
</script>
