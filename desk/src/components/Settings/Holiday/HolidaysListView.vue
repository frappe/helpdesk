<template>
  <div class="rounded-md border p-1 border-gray-300 text-sm">
    <div
      class="grid p-2 items-center gap-2"
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
    <hr class="my-0.5" />
    <div v-for="(holiday, index) in holidays" :key="holiday.name">
      <div
        class="grid gap-2 px-2 items-center"
        :style="{ gridTemplateColumns: '1fr 4fr 22px' }"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
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
          <Dropdown
            placement="right"
            :options="[
              {
                label: 'Edit',
                onClick: () => editHoliday(holiday),
                icon: 'edit',
              },
              {
                label: 'Confirm Delete',
                component: (props) =>
                  TemplateOption({
                    option: isConfirmingDelete ? 'Confirm Delete' : 'Delete',
                    icon: 'trash-2',
                    active: props.active,
                    variant: isConfirmingDelete ? 'danger' : 'gray',
                    onClick: (event) => deleteHoliday(event, holiday),
                  }),
              },
            ]"
          >
            <Button
              icon="more-horizontal"
              variant="ghost"
              @click="isConfirmingDelete = false"
            />
          </Dropdown>
        </div>
      </div>
      <hr class="my-0.5" v-if="index !== holidays.length - 1" />
    </div>
    <div v-if="holidays?.length === 0" class="text-center p-4 text-gray-600">
      No items in the list
    </div>
  </div>
  <Dialog v-model="dialog" :options="{ size: 'sm', title: 'Edit Holiday' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Date" required />
          <DatePicker
            v-model="editHolidayData.holiday_date"
            variant="subtle"
            placeholder="Date"
            class="w-full"
            id="holiday_date"
            required
            :formatter="(date) => getFormattedDate(date)"
          />
        </div>
        <FormControl
          :type="'textarea'"
          size="sm"
          variant="subtle"
          placeholder="Description"
          label="Description"
          v-model="editHolidayData.description"
          required
        />
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        @click="saveHoliday"
        class="w-full"
        label="Update Holiday"
        icon-left="edit-2"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Dropdown, DatePicker, FormControl, FormLabel } from "frappe-ui";
import dayjs from "dayjs";
import { getFormattedDate, TemplateOption } from "@/utils";
import { holidayData } from "@/stores/holidayList";

const isConfirmingDelete = ref(false);

interface Holiday {
  holiday_date: string | null;
  description: string;
  weekly_off?: number;
}

const dialog = ref(false);
const editHolidayData = ref<Holiday>({
  holiday_date: null,
  description: "",
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
  dialog.value = true;
  editHolidayData.value = { ...holiday };
};

const saveHoliday = () => {
  if (
    !editHolidayData.value.holiday_date ||
    !editHolidayData.value.description
  ) {
    return;
  }

  const index = holidayData.value.holidays.findIndex(
    (h: Holiday) =>
      getFormattedDate(h.holiday_date) ===
      getFormattedDate(editHolidayData.value.holiday_date)
  );

  if (index !== -1) {
    holidayData.value.holidays.splice(index, 1, {
      ...editHolidayData.value,
      weekly_off: 0,
    });
    dialog.value = false;
    editHolidayData.value = { holiday_date: null, description: "" };
  }
};

const deleteHoliday = (event, holidayToDelete?: Holiday) => {
  event.preventDefault();

  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  const index = holidayData.value.holidays.findIndex((h: Holiday) => {
    const holidayDate = getFormattedDate(h.holiday_date);
    const editDate = getFormattedDate(holidayToDelete.holiday_date);
    return holidayDate === editDate;
  });

  holidayData.value.holidays.splice(index, 1);
  dialog.value = false;
  editHolidayData.value = { holiday_date: null, description: "" };
  isConfirmingDelete.value = false;
};
</script>
