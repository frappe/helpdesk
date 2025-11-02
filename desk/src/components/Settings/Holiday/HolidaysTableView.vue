<template>
  <div class="rounded-md border px-2 border-gray-300 text-sm">
    <div
      class="grid p-2 px-4 items-center gap-2"
      :style="{
        gridTemplateColumns: '1fr 4fr 22px',
      }"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
      </div>
    </div>
    <hr />
    <div v-for="(holiday, index) in holidays" :key="holiday.name">
      <div
        class="grid gap-2 py-3.5 px-4 items-center"
        :style="{ gridTemplateColumns: '1fr 4fr 22px' }"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="w-full overflow-hidden whitespace-nowrap text-ellipsis"
        >
          <input
            v-if="column.key === 'description'"
            :type="'text'"
            placeholder="Description"
            v-model="holiday[column.key]"
            class="!bg-white w-full text-base px-0 focus:!ring-0 border-none hover:bg-white outline-none no-underline focus:!outline-none"
          />
          <div v-else>
            {{ dayjs(holiday[column.key]).format("DD MMM YYYY") }}
          </div>
        </div>
        <div class="flex justify-end">
          <Dropdown placement="right" :options="dropdownOptions(holiday)">
            <Button
              icon="more-horizontal"
              variant="ghost"
              @click="isConfirmingDelete = false"
            />
          </Dropdown>
        </div>
      </div>
      <hr v-if="index !== holidays.length - 1" />
    </div>
    <div v-if="holidays?.length === 0" class="text-center p-4 text-gray-600">
      No items in the list
    </div>
  </div>
  <AddHolidayModal v-model="dialog" />
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import dayjs from "dayjs";
import { ConfirmDelete, getFormattedDate } from "@/utils";
import { holidayData } from "@/stores/holidayList";
import AddHolidayModal from "./Modals/AddHolidayModal.vue";

const isConfirmingDelete = ref(false);

interface Holiday {
  holiday_date: string | null;
  description: string;
  weekly_off?: number;
}

const dropdownOptions = (holiday: Holiday) => [
  {
    label: "Edit",
    onClick: () => editHoliday(holiday),
    icon: "edit",
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteHoliday(holiday),
    isConfirmingDelete,
  }),
];

const dialog = ref({
  show: false,
  holiday_date: null,
  description: "",
  editing: null,
});

const holidays = computed(() => {
  return holidayData.value.holidays.filter((item) => {
    return item.weekly_off == 0;
  });
});

const columns = [
  {
    label: "Date",
    key: "holiday_date",
  },
  {
    label: "Description",
    key: "description",
  },
];

const editHoliday = (holiday: Holiday) => {
  dialog.value = {
    show: true,
    holiday_date: holiday.holiday_date,
    description: holiday.description,
    editing: holiday,
  };
};

const deleteHoliday = (holidayToDelete?: Holiday) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  const index = holidayData.value.holidays.findIndex((h: Holiday) => {
    const holidayDate = getFormattedDate(h.holiday_date);
    const editDate = getFormattedDate(holidayToDelete?.holiday_date);
    return holidayDate === editDate;
  });

  holidayData.value.holidays.splice(index, 1);
  isConfirmingDelete.value = false;
};
</script>
