<template>
  <div
    v-if="holidayData.loading"
    class="flex items-center h-full justify-center"
  >
    <Spinner class="w-8" />
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
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5"
        />
      </div>
    </div>
    <Button label="Save" theme="gray" variant="solid" @click="saveHoliday()" />
  </div>
  <div v-if="!holidayData.loading" class="px-10 pb-8 overflow-y-scroll h-full">
    <div class="flex items-center gap-2 mt-2">
      <span class="text-sm">
        There are in total <b>{{ holidayData.holidays.length }}</b> holidays in
        this list</span
      >
    </div>
    <hr class="mb-6 mt-3" />
    <div class="grid grid-cols-2 gap-2">
      <div>
        <FormControl
          :type="'text'"
          size="sm"
          variant="subtle"
          placeholder="Name"
          label="Name"
          v-model="holidayData.holiday_list_name"
          required
          @change="debouncedValidateHoliday()"
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
        <span class="text-lg font-medium">Valid from</span>
        <span class="text-sm text-gray-600">
          Choose the duration of this holiday list.
        </span>
      </div>
      <div class="mt-4 flex gap-2">
        <div class="w-full space-y-1.5">
          <FormLabel label="From date" for="from_date" required />
          <DatePicker
            v-model="holidayData.from_date"
            variant="subtle"
            placeholder="From date"
            class="w-full"
            id="from_date"
            :formatter="(date) => getFormat(date)"
            @change="debouncedUpdateDuration()"
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
            :formatter="(date) => getFormat(date)"
            @change="debouncedUpdateDuration()"
          />
          <div
            v-if="holidayDataErrors.end_date"
            class="text-red-500 text-xs mt-1"
          >
            {{ holidayDataErrors.end_date }}
          </div>
        </div>
      </div>
    </div>
    <hr class="my-6" />
    <div>
      <div class="flex flex-col gap-2">
        <div class="text-lg font-medium">Recurring holidays</div>
        <div class="text-sm text-gray-600">
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
        <span class="text-lg font-medium">Holidays</span>
        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-600">
            Add holidays here to make sure they’re excluded from SLA
            calculations.
          </div>
          <TabButtons
            :buttons="[
              {
                value: 'list',
                icon: 'list',
              },
              {
                value: 'calendar',
                icon: 'calendar',
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
</template>

<script setup lang="ts">
import {
  holidayData,
  holidayDataErrors,
  holidayListActiveScreen,
  resetHolidayData,
  updateWeeklyOffDates,
  validateHoliday,
} from "./holidayList";
import {
  createResource,
  TabButtons,
  DatePicker,
  Button,
  FormControl,
  toast,
  Spinner,
} from "frappe-ui";
import { onUnmounted, ref } from "vue";
import HolidaysListView from "./HolidaysListView.vue";
import RecurringHolidaysList from "./RecurringHolidaysList.vue";

import HolidaysCalendarView from "./HolidaysCalendarView.vue";
import AddHolidayModal from "./AddHolidayModal.vue";
import { getFormat, htmlToText } from "@/utils";
import FormLabel from "frappe-ui/src/components/FormLabel.vue";
import { useDebounceFn } from "@vueuse/core";
import dayjs from "dayjs";
import { activeTab, tabs } from "../settingsModal";
import { slaActiveScreen } from "../Sla/sla";

const dialog = ref(false);

const holidayListView = ref("list");

const getHolidayData = createResource({
  url: "helpdesk.api.holiday_list.get_holiday_list",
  params: {
    docname: holidayListActiveScreen.value.data?.name,
  },
  onSuccess(data) {
    holidayData.value = data;
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

const debouncedValidateHoliday = useDebounceFn(() => validateHoliday(), 300);

const updateDuration = () => {
  validateHoliday();
  if (
    !holidayDataErrors.value.dateRange ||
    holidayDataErrors.value.dateRange === ""
  ) {
    updateWeeklyOffDates();
  }
};

const debouncedUpdateDuration = useDebounceFn(() => updateDuration(), 300);

const goBack = () => {
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
  if (!validateHoliday()) {
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
      toast.success("Holiday created successfully");
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
    url: "frappe.client.set_value",
    params: {
      doctype: "HD Service Holiday List",
      name: holidayListActiveScreen.value.data.name,
      fieldname: {
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
    onSuccess() {
      toast.success("Holiday updated successfully");
    },
  });
};

onUnmounted(() => {
  resetHolidayData();
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
