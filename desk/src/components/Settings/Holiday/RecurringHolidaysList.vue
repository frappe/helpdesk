<template>
  <div class="rounded-md border p-1 border-gray-300 text-sm">
    <div
      class="grid p-2 items-center"
      :style="{
        gridTemplateColumns: '1fr 4fr 22px',
      }"
      v-if="holidays?.length !== 0"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
      >
        {{ column.label }}
      </div>
    </div>
    <hr class="my-0.5" v-if="holidays?.length !== 0" />
    <div v-for="(holiday, index) in holidays" :key="holiday.day">
      <div
        class="grid gap-2 px-2 py-2 items-center"
        :style="{ gridTemplateColumns: '1fr 4fr 22px' }"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="w-full py-2 overflow-hidden whitespace-nowrap text-ellipsis"
        >
          <div v-if="column.key === 'repetition'">
            {{ getRepetitionText(holiday[column.key]) }}
          </div>
          <div v-else>{{ holiday[column.key] }}</div>
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
  <Button
    variant="subtle"
    @click="addHoliday"
    class="mt-4"
    label="Add Recurring Holiday"
    icon-left="plus"
  />
  <Dialog v-model="dialog" :options="{ size: 'md' }">
    <template #body-title>
      <h3 class="text-2xl font-semibold">
        {{ recurringHolidayData.isEditing ? "Edit" : "Add" }} Recurring Holiday
      </h3>
    </template>
    <template #body-content>
      <div v-if="!props.holidayData.from_date || !props.holidayData.to_date">
        <div class="text-center p-4 text-gray-600">
          Please select start and end date first
        </div>
      </div>
      <div v-else class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Day" required />
          <Select
            :options="availableWorkDays"
            v-model="recurringHolidayData.day"
            :disabled="availableWorkDays.length === 0"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormLabel label="Repetition" required />
          <div class="grid grid-cols-2 gap-2 mt-2">
            <Checkbox
              v-model="recurringHolidayData.repetition.all"
              label="Every week"
              :disabled="
                recurringHolidayData.repetition.first ||
                recurringHolidayData.repetition.second ||
                recurringHolidayData.repetition.third ||
                recurringHolidayData.repetition.fourth
              "
            />
            <Checkbox
              v-model="recurringHolidayData.repetition.first"
              label="Every first week"
              :disabled="recurringHolidayData.repetition.all"
            />
            <Checkbox
              v-model="recurringHolidayData.repetition.second"
              label="Every second week"
              :disabled="recurringHolidayData.repetition.all"
            />
            <Checkbox
              v-model="recurringHolidayData.repetition.third"
              label="Every third week"
              :disabled="recurringHolidayData.repetition.all"
            />
            <Checkbox
              v-model="recurringHolidayData.repetition.fourth"
              label="Every fourth week"
              :disabled="recurringHolidayData.repetition.all"
            />
            <Checkbox
              v-model="recurringHolidayData.repetition.fifth"
              label="Every fifth week"
              :disabled="recurringHolidayData.repetition.all"
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        @click="saveHoliday"
        class="w-full"
        v-if="props.holidayData.from_date && props.holidayData.to_date"
        :label="
          recurringHolidayData.isEditing ? 'Update Holiday' : 'Add Holiday'
        "
        :icon-left="recurringHolidayData.isEditing ? 'edit-2' : 'plus'"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { Select, FormLabel, Checkbox, toast, Dropdown } from "frappe-ui";
import dayjs from "dayjs";
import weekday from "dayjs/plugin/weekday";
import isSameOrBefore from "dayjs/plugin/isSameOrBefore";
import { updateWeeklyOffDates } from "@/stores/holidayList";
import { TemplateOption } from "@/utils";

dayjs.extend(weekday);
dayjs.extend(isSameOrBefore);

const dialog = ref(false);
const recurringHolidayData = ref({
  day: null,
  repetition: {
    all: false,
    first: false,
    second: false,
    third: false,
    fourth: false,
    fifth: false,
  },
  isEditing: false,
});

const props = defineProps({
  holidays: {
    type: Array<any>,
    default: () => [],
    required: true,
  },
  holidayData: {
    type: Object,
    default: () => {},
    required: true,
  },
});

const columns = [
  {
    label: "Day",
    key: "day",
  },
  {
    label: "Repetition",
    key: "repetition",
  },
];

const workDays = ref([
  {
    label: "Monday",
    value: "Monday",
  },
  {
    label: "Tuesday",
    value: "Tuesday",
  },
  {
    label: "Wednesday",
    value: "Wednesday",
  },
  {
    label: "Thursday",
    value: "Thursday",
  },
  {
    label: "Friday",
    value: "Friday",
  },
  {
    label: "Saturday",
    value: "Saturday",
  },
  {
    label: "Sunday",
    value: "Sunday",
  },
]);

const availableWorkDays = computed(() => {
  const usedDays = new Set(props.holidays.map((h) => h.day));
  return workDays.value.filter((day) => !usedDays.has(day.value));
});

const isConfirmingDelete = ref(false);

const getRepetitionText = (repetition: any) => {
  const parts: string[] = [];

  if (repetition.all) {
    parts.push("week");
  } else {
    if (repetition.first) parts.push("first");
    if (repetition.second) parts.push("second");
    if (repetition.third) parts.push("third");
    if (repetition.fourth) parts.push("fourth");
    if (repetition.fifth) parts.push("fifth");

    if (parts.length === 0) return "";

    if (parts.length > 1) {
      const last = parts.pop();
      parts[parts.length - 1] = `${parts[parts.length - 1]} and ${last}`;
    }

    parts[0] = parts[0].charAt(0) + parts[0].slice(1);
    return `Every ${parts.join(", ")} week`;
  }

  return parts[0] ? `Every ${parts[0]}` : "";
};

const addHoliday = () => {
  recurringHolidayData.value = {
    day: null,
    repetition: {
      all: false,
      first: false,
      second: false,
      third: false,
      fourth: false,
      fifth: false,
    },
    isEditing: false,
  };
  dialog.value = true;
};

const editHoliday = (holiday: any) => {
  recurringHolidayData.value = holiday;
  recurringHolidayData.value.isEditing = true;
  dialog.value = true;
};

const saveHoliday = () => {
  if (!recurringHolidayData.value.day) {
    toast.error("Please select a day of the week");
    return;
  }

  const { all, first, second, third, fourth, fifth } =
    recurringHolidayData.value.repetition;
  if (!all && !first && !second && !third && !fourth && !fifth) {
    toast.error("Please select at least one repetition option");
    return;
  }

  const index = props.holidays.findIndex((h: any) => {
    return h.day === recurringHolidayData.value.day;
  });

  if (recurringHolidayData.value.isEditing) {
    props.holidays.splice(index, 1, {
      ...recurringHolidayData.value,
    });
    updateWeeklyOffDates();
  } else {
    if (index !== -1) {
      toast.error("Holiday already exists");
      return;
    }
    props.holidays.push({
      ...recurringHolidayData.value,
    });
    updateWeeklyOffDates();
  }
  dialog.value = false;
};

const deleteHoliday = (event, holiday: any) => {
  event.stopPropagation();
  event.preventDefault();
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  const index = props.holidays.findIndex((h: any) => {
    return h.day === holiday.day;
  });
  props.holidays.splice(index, 1);
  updateWeeklyOffDates();
  dialog.value = false;
  isConfirmingDelete.value = false;
};
</script>
