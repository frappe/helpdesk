<template>
  <div
    v-if="holidayData.loading"
    class="flex items-center h-full justify-center"
  >
    <LoadingIndicator class="w-4" />
  </div>
  <div
    v-if="!holidayData.loading"
    class="flex items-center justify-between sticky top-0 z-10 bg-white px-10 pt-8 pb-4"
  >
    <div>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="holidayData?.holiday_list_name || 'New Business Holiday'"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0"
        />
        <Badge
          :variant="'subtle'"
          :theme="'orange'"
          size="sm"
          label="Unsaved changes"
          v-if="isDirty"
        />
      </div>
    </div>
    <div class="flex gap-2 items-center">
      <Button
        label="Save"
        theme="gray"
        variant="solid"
        @click="saveHoliday()"
        :disabled="Boolean(!isDirty && holidayListActiveScreen.data)"
        :loading="
          holidayList.loading ||
          updateHolidayResource.loading ||
          getHolidayData.loading
        "
      />
    </div>
  </div>

  <div v-if="!holidayData.loading" class="px-10 pb-8 overflow-y-scroll h-full">
    <div class="flex items-center gap-2 mt-2">
      <span class="text-sm">
        There are in total <b>{{ holidayData.holidays.length }}</b> holidays in
        this list</span
      >
    </div>
    <hr class="mb-8 mt-2" />
    <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="holidayData.holiday_list_name"
          required
          @change="validateHoliday('holiday_list_name')"
        />
        <ErrorMessage
          :message="holidayDataErrors.holiday_list_name"
          class="mt-2"
        />
      </div>
      <FormControl
        :type="'textarea'"
        size="sm"
        variant="subtle"
        placeholder="Description"
        label="Description"
        v-model="holidayData.description"
      />
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex flex-col gap-1">
        <span class="text-lg font-semibold text-ink-gray-8">Valid from</span>
        <span class="text-p-sm text-ink-gray-6">
          Choose the duration of this holiday list.
        </span>
      </div>
      <div class="mt-3.5 flex gap-5 flex-col md:flex-row">
        <div class="w-full space-y-1.5">
          <FormLabel label="From date" for="from_date" required />
          <DatePicker
            v-model="holidayData.from_date"
            variant="subtle"
            placeholder="11/01/2025"
            class="w-full"
            id="from_date"
            :formatter="(date) => getFormattedDate(date)"
            :debounce="300"
            @update:model-value="updateDuration('from_date')"
          >
            <template #prefix>
              <LucideCalendar class="size-4" />
            </template>
          </DatePicker>
          <ErrorMessage
            :message="
              holidayDataErrors.from_date || holidayDataErrors.dateRange
            "
          />
        </div>
        <div class="w-full space-y-1.5">
          <FormLabel label="To date" for="to_date" required />
          <DatePicker
            v-model="holidayData.to_date"
            variant="subtle"
            placeholder="25/12/2025"
            class="w-full"
            id="to_date"
            :formatter="(date) => getFormattedDate(date)"
            :debounce="300"
            @update:model-value="updateDuration('to_date')"
          >
            <template #prefix>
              <LucideCalendar class="size-4" />
            </template>
          </DatePicker>
          <ErrorMessage :message="holidayDataErrors.to_date" />
        </div>
      </div>
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex flex-col gap-1">
        <div class="text-lg font-semibold text-ink-gray-8">
          Recurring holidays
        </div>
        <div class="text-p-sm text-ink-gray-6">
          Add recurring holidays such as weekends.
        </div>
      </div>
      <div class="mt-5">
        <RecurringHolidaysList
          :holidayData="holidayData"
          :holidays="holidayData.recurring_holidays"
        />
      </div>
    </div>
    <hr class="my-8" />
    <div>
      <div class="flex justify-between items-center">
        <div class="flex justify-between flex-col gap-1">
          <span class="text-lg font-semibold text-ink-gray-8">Holidays</span>
          <div class="text-p-sm text-ink-gray-6">
            Add holidays here to make sure they’re excluded from SLA
            calculations.
          </div>
        </div>
        <TabButtons
          :buttons="[
            {
              value: 'calendar',
              icon: 'calendar',
            },
            {
              value: 'list',
              icon: 'list',
            },
          ]"
          v-model="holidayListView"
        />
      </div>
      <div class="mt-5">
        <HolidaysTableView v-if="holidayListView === 'list'" />
        <HolidaysCalendarView v-else />
      </div>
      <div class="mt-2.5 flex justify-between items-center">
        <Button
          variant="subtle"
          label="Add Holiday"
          @click="dialog.show = true"
          icon-left="plus"
        />
        <!-- Indicators -->
        <div class="flex gap-4" v-if="holidayListView === 'calendar'">
          <div class="gap-1 flex items-center">
            <span class="bg-yellow-100 size-4 rounded-sm" />
            <span class="text-sm text-ink-gray-6">Holidays</span>
          </div>
          <div class="gap-1 flex items-center">
            <span class="bg-gray-100 size-4 rounded-sm" />
            <span class="text-sm text-ink-gray-6">Recurring holidays</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  <AddHolidayModal v-model="dialog" />
  <ConfirmDialog
    v-model="showConfirmDialog"
    title="Unsaved changes"
    message="Are you sure you want to go back? Unsaved changes will be lost."
    :onConfirm="goBack"
    :onCancel="() => (showConfirmDialog = false)"
  />
</template>

<script setup lang="ts">
import {
  holidayData,
  holidayDataErrors,
  holidayListActiveScreen,
  updateWeeklyOffDates,
  validateHoliday,
} from "@/stores/holidayList";
import {
  Button,
  createResource,
  DatePicker,
  FormControl,
  LoadingIndicator,
  TabButtons,
  toast,
} from "frappe-ui";
import { inject, onMounted, onUnmounted, ref, watch } from "vue";
import HolidaysTableView from "./HolidaysTableView.vue";
import RecurringHolidaysList from "./RecurringHolidaysList.vue";

import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { slaActiveScreen } from "@/stores/sla";
import { getFormattedDate, htmlToText } from "@/utils";
import dayjs from "dayjs";
import FormLabel from "frappe-ui/src/components/FormLabel.vue";
import {
  disableSettingModalOutsideClick,
  setActiveSettingsTab,
} from "../settingsModal";
import HolidaysCalendarView from "./HolidaysCalendarView.vue";
import AddHolidayModal from "./Modals/AddHolidayModal.vue";

const dialog = ref({
  show: false,
  holiday_date: new Date(),
  description: "",
  editing: null,
});

const isDirty = ref(false);
const initialData = ref(null);
const holidayListView = ref("calendar");

const showConfirmDialog = ref(false);

const holidayList = inject<any>("holidayList");

const getHolidayData = createResource({
  url: "helpdesk.api.holiday_list.get_holiday_list",
  params: {
    docname: holidayListActiveScreen.value.data?.name,
  },
  onSuccess(data) {
    holidayData.value = data;
    initialData.value = JSON.stringify(data);
  },
  transform(data) {
    for (let holiday of data.holidays) {
      holiday.description = htmlToText(holiday.description);
    }
    data.recurring_holidays = JSON.parse(data.recurring_holidays || "[]");
    return data;
  },
});

if (holidayListActiveScreen.value.data?.name) {
  holidayData.value.loading = true;
  getHolidayData.fetch();
} else {
  disableSettingModalOutsideClick.value = true;
}

const updateDuration = (key) => {
  validateHoliday(key);
  if (
    !holidayDataErrors.value.dateRange ||
    holidayDataErrors.value.dateRange === ""
  ) {
    updateWeeklyOffDates();
  }
};

const goBack = () => {
  if (isDirty.value && !showConfirmDialog.value) {
    showConfirmDialog.value = true;
    return;
  }
  if (!holidayListActiveScreen.value.data && !showConfirmDialog.value) {
    showConfirmDialog.value = true;
    return;
  }
  if (holidayListActiveScreen.value.previousScreen) {
    setActiveSettingsTab("SLA Policies");

    slaActiveScreen.value = {
      screen: "view",
      data: { name: holidayListActiveScreen.value.previousScreen.data },
      fetchData: false,
    };
  }
  showConfirmDialog.value = false;
  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    holidayListActiveScreen.value = {
      screen: "list",
      data: null,
    };
  }, 250);
};

const saveHoliday = () => {
  const validationErrors = validateHoliday();
  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      "Invalid fields, check if all are filled in and values are correct."
    );
    return;
  }

  if (holidayListActiveScreen.value.data) {
    updateHoliday();
  } else {
    createHoliday();
  }
};

const createHoliday = () => {
  const holidays = holidayData.value.holidays.map((holiday) => {
    return {
      ...holiday,
      holiday_date: dayjs(holiday.holiday_date).format("YYYY-MM-DD"),
    };
  });
  holidayList.insert.submit(
    {
      holiday_list_name: holidayData.value.holiday_list_name,
      description: holidayData.value.description,
      from_date: holidayData.value.from_date,
      to_date: holidayData.value.to_date,
      holidays: holidays,
      recurring_holidays: JSON.stringify(holidayData.value.recurring_holidays),
    },
    {
      onSuccess(data) {
        toast.success("Holiday list created");
        holidayListActiveScreen.value.data = data;
        holidayListActiveScreen.value.screen = "view";
        getHolidayData.submit({
          docname: data.name,
        });
      },
    }
  );
};

const updateHolidayResource = createResource({
  url: "helpdesk.api.holiday_list.update_holiday_list",
  onSuccess(data) {
    holidayListActiveScreen.value.data = data;
    getHolidayData.submit({
      docname: data.name,
    });
    toast.success("Holiday list updated");
  },
});

const updateHoliday = () => {
  const holidays = holidayData.value.holidays.map((holiday) => {
    return {
      ...holiday,
      holiday_date: dayjs(holiday.holiday_date).format("YYYY-MM-DD"),
    };
  });

  updateHolidayResource.submit({
    docname: holidayListActiveScreen.value.data.name,
    doc: {
      holiday_list_name: holidayData.value.holiday_list_name,
      description: holidayData.value.description,
      from_date: holidayData.value.from_date,
      to_date: holidayData.value.to_date,
      holidays: holidays,
      recurring_holidays: JSON.stringify(holidayData.value.recurring_holidays),
    },
  });
};

watch(
  holidayData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value = JSON.stringify(newVal) != initialData.value;
    if (isDirty.value) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);

const beforeUnloadHandler = (event) => {
  if (!isDirty.value) return;
  event.preventDefault();
  event.returnValue = true;
};

onMounted(() => {
  addEventListener("beforeunload", beforeUnloadHandler);
});

onUnmounted(() => {
  removeEventListener("beforeunload", beforeUnloadHandler);
  holidayDataErrors.value = {
    holiday_list_name: "",
    from_date: "",
    to_date: "",
  };
  disableSettingModalOutsideClick.value = false;
});
</script>

<style scoped>
input[type="radio"] {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  border: 2px solid #c5c2c2;
  border-radius: 50%;
  outline: none;
  transition: all 0.2s ease;
  background-color: white;
}

input[type="radio"]:checked {
  background-color: black;
  border: 2px solid #000;
}

input[type="radio"]:checked::after {
  content: "";
  background-color: #fff;
}

input[type="radio"]:focus {
  outline: none !important;
  box-shadow: none !important;
}
</style>
