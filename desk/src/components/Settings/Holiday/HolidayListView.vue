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
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl"
        />
      </div>
    </div>
    <div class="flex gap-2 items-center">
      <Badge
        :variant="'subtle'"
        :theme="'orange'"
        size="sm"
        label="Unsaved changes"
        v-if="isDirty"
      />
      <Button
        label="Save"
        theme="gray"
        variant="solid"
        @click="saveHoliday()"
        :disabled="Boolean(!isDirty && holidayListActiveScreen.data)"
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
    <hr class="mb-6 mt-3" />
    <div class="grid grid-cols-2 gap-5">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="holidayData.holiday_list_name"
          required
          @change="debouncedValidateHoliday('holiday_list_name')"
        />
        <div
          v-if="holidayDataErrors.holiday_list_name"
          class="text-red-500 text-xs mt-1"
        >
          {{ holidayDataErrors.holiday_list_name }}
        </div>
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
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <span class="text-lg font-semibold text-ink-gray-7">Valid from</span>
        <span class="text-sm text-ink-gray-6">
          Choose the duration of this holiday list.
        </span>
      </div>
      <div class="mt-4 flex gap-5">
        <div class="w-full space-y-1.5">
          <FormLabel label="From date" for="from_date" required />
          <DatePicker
            v-model="holidayData.from_date"
            variant="subtle"
            placeholder="From date"
            class="w-full"
            id="from_date"
            :formatter="(date) => getFormattedDate(date)"
            @change="debouncedUpdateDuration('from_date')"
          />
          <div
            v-if="holidayDataErrors.from_date"
            class="text-red-500 text-xs mt-1"
          >
            {{ holidayDataErrors.from_date }}
          </div>
          <div
            v-if="holidayDataErrors.dateRange"
            class="text-red-500 text-xs mt-1"
          >
            {{ holidayDataErrors.dateRange }}
          </div>
        </div>
        <div class="w-full space-y-1.5">
          <FormLabel label="To date" for="to_date" required />
          <DatePicker
            v-model="holidayData.to_date"
            variant="subtle"
            placeholder="To date"
            class="w-full"
            id="to_date"
            :formatter="(date) => getFormattedDate(date)"
            @change="debouncedUpdateDuration('to_date')"
          />
          <div
            v-if="holidayDataErrors.to_date"
            class="text-red-500 text-xs mt-1"
          >
            {{ holidayDataErrors.to_date }}
          </div>
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <div class="text-lg font-semibold text-ink-gray-7">
          Recurring holidays
        </div>
        <div class="text-sm text-ink-gray-6">
          Add recurring holidays such as weekends.
        </div>
      </div>
      <div class="mt-6">
        <RecurringHolidaysList
          :holidayData="holidayData"
          :holidays="holidayData.recurring_holidays"
        />
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-1">
        <span class="text-lg font-semibold text-ink-gray-7">Holidays</span>
        <div class="flex items-center justify-between">
          <div class="text-sm text-ink-gray-6">
            Add holidays here to make sure they’re excluded from SLA
            calculations.
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
      </div>
      <div class="mt-4">
        <HolidaysListView
          v-if="holidayListView === 'list'"
          :holidayData="holidayData"
        />
        <HolidaysCalendarView :holidayData="holidayData" v-else />
      </div>
      <div class="mt-4">
        <Button
          variant="subtle"
          label="Add Holiday"
          @click="dialog = true"
          icon-left="plus"
        />
        <AddHolidayModal
          v-model="dialog"
          :holidays="holidayData.holidays"
          :from_date="holidayData.from_date"
          :to_date="holidayData.to_date"
        />
      </div>
    </div>
  </div>
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
  createResource,
  TabButtons,
  DatePicker,
  Button,
  FormControl,
  toast,
  LoadingIndicator,
} from "frappe-ui";
import { onMounted, onUnmounted, ref, watch } from "vue";
import HolidaysListView from "./HolidaysListView.vue";
import RecurringHolidaysList from "./RecurringHolidaysList.vue";

import HolidaysCalendarView from "./HolidaysCalendarView.vue";
import AddHolidayModal from "./AddHolidayModal.vue";
import { getFormattedDate, htmlToText } from "@/utils";
import FormLabel from "frappe-ui/src/components/FormLabel.vue";
import { useDebounceFn } from "@vueuse/core";
import dayjs from "dayjs";
import { activeTab, tabs } from "../settingsModal";
import { slaActiveScreen } from "@/stores/sla";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

const dialog = ref(false);

const isDirty = ref(false);
const initialData = ref(null);
const holidayListView = ref("calendar");

const showConfirmDialog = ref(false);

const getHolidayData = createResource({
  url: "helpdesk.api.holiday_list.get_holiday_list",
  params: {
    docname: holidayListActiveScreen.value.data?.name,
  },
  onSuccess(data) {
    holidayData.value = data;
    initialData.value = JSON.parse(JSON.stringify(data));
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
}

const debouncedValidateHoliday = useDebounceFn(
  (key) => validateHoliday(key),
  300
);

const updateDuration = (key) => {
  validateHoliday(key);
  if (
    !holidayDataErrors.value.dateRange ||
    holidayDataErrors.value.dateRange === ""
  ) {
    updateWeeklyOffDates();
  }
};

const debouncedUpdateDuration = useDebounceFn(
  (key) => updateDuration(key),
  300
);

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
    activeTab.value = tabs[4];

    slaActiveScreen.value = {
      screen: "view",
      data: { name: holidayListActiveScreen.value.previousScreen.data },
      fetchData: false,
    };
    holidayListActiveScreen.value = {
      screen: "list",
      data: null,
    };
    return;
  }
  holidayListActiveScreen.value = {
    screen: "list",
    data: null,
  };
};

const saveHoliday = () => {
  const validationErrors = validateHoliday();
  if (Object.values(validationErrors).some((error) => error)) {
    toast.error("Please provide all required fields");
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
  createResource({
    url: "frappe.client.insert",
    params: {
      doc: {
        doctype: "HD Service Holiday List",
        holiday_list_name: holidayData.value.holiday_list_name,
        description: holidayData.value.description,
        from_date: holidayData.value.from_date,
        to_date: holidayData.value.to_date,
        holidays: holidays,
        recurring_holidays: JSON.stringify(
          holidayData.value.recurring_holidays
        ),
      },
    },
    auto: true,
    onSuccess(data) {
      toast.success("Holiday list created");
      holidayListActiveScreen.value.data = data;
      holidayListActiveScreen.value.screen = "view";
      getHolidayData.submit({
        docname: data.name,
      });
    },
  });
};

const updateHoliday = () => {
  const holidays = holidayData.value.holidays.map((holiday) => {
    return {
      ...holiday,
      holiday_date: dayjs(holiday.holiday_date).format("YYYY-MM-DD"),
    };
  });
  createResource({
    url: "helpdesk.api.holiday_list.update_holiday_list",
    params: {
      docname: holidayListActiveScreen.value.data.name,
      doc: {
        holiday_list_name: holidayData.value.holiday_list_name,
        description: holidayData.value.description,
        from_date: holidayData.value.from_date,
        to_date: holidayData.value.to_date,
        holidays: holidays,
        recurring_holidays: JSON.stringify(
          holidayData.value.recurring_holidays
        ),
      },
    },
    auto: true,
    onSuccess(data) {
      holidayListActiveScreen.value.data = data;
      getHolidayData.submit({
        docname: data.name,
      });
      toast.success("Holiday list updated");
    },
  });
};

watch(
  holidayData,
  (newVal) => {
    if (!initialData.value) return;
    isDirty.value =
      JSON.stringify(Object.assign({}, newVal)) !=
      JSON.stringify(Object.assign({}, initialData.value));
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
