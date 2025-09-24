<template>
  <SettingsHeader :routes="routes" />
  <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
    <div
      v-if="!holidayData.loading"
      class="flex items-center justify-between bg-white pb-6"
    >
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="holidayData?.holiday_list_name || 'New Business Holiday'"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0 max-w-48 md:max-w-60 lg:max-w-max overflow-ellipsis overflow-hidden"
        />
        <Badge
          :variant="'subtle'"
          :theme="'orange'"
          size="sm"
          label="Unsaved changes"
          v-if="isDirty"
        />
      </div>
      <div class="flex gap-2 items-center">
        <Button
          label="Save"
          theme="gray"
          variant="solid"
          @click="saveHoliday()"
          :disabled="Boolean(!isDirty)"
        />
      </div>
    </div>

    <div v-if="!holidayData.loading" class="overflow-y-auto">
      <div class="flex items-center gap-2 mt-2">
        <span class="text-sm">
          There are in total <b>{{ holidayData.holidays.length }}</b> holidays
          in this list</span
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
        <div
          class="mt-2.5 flex justify-between sm:items-center flex-col-reverse sm:flex-row gap-2"
        >
          <Button
            variant="subtle"
            label="Add Holiday"
            @click="dialog.show = true"
            icon-left="plus"
            class="w-max"
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
  </div>
</template>

<script setup lang="ts">
import {
  holidayData,
  holidayDataErrors,
  updateWeeklyOffDates,
  validateHoliday,
} from "@/stores/holidayList";
import {
  Button,
  createResource,
  DatePicker,
  FormControl,
  TabButtons,
  toast,
} from "frappe-ui";
import { computed, provide, ref, watch } from "vue";
import HolidaysTableView from "./components/HolidaysTableView.vue";
import RecurringHolidaysList from "./components/RecurringHolidaysList.vue";

import { getFormattedDate } from "@/utils";
import dayjs from "dayjs";
import FormLabel from "frappe-ui/src/components/FormLabel.vue";
import HolidaysCalendarView from "./components/HolidaysCalendarView.vue";
import AddHolidayModal from "./Modals/AddHolidayModal.vue";
import { onBeforeRouteLeave, useRouter } from "vue-router";
import SettingsHeader from "../components/SettingsHeader.vue";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";

const { $dialog } = globalStore();

const router = useRouter();
const dialog = ref({
  show: false,
  holiday_date: new Date(),
  description: "",
  editing: null,
});
const isDirty = ref(false);
const initialData = ref(JSON.stringify(holidayData.value));
const holidayListView = ref("calendar");

const goBack = () => {
  const previousPage = router.currentRoute.value.query.previousPage as string;
  if (previousPage) {
    router.push({
      path: previousPage,
      query: { fetchData: "false" },
    });
    return;
  }
  router.push({ name: "BusinessHolidays" });
};

const routes = computed(() => [
  {
    label: "Business Holidays",
    to: "/settings/holiday-list",
  },
  {
    label: holidayData.value?.holiday_list_name || "New Business Holidays",
    to: "/settings/holiday-list/new",
  },
]);

const updateDuration = (key) => {
  validateHoliday(key);
  if (
    !holidayDataErrors.value.dateRange ||
    holidayDataErrors.value.dateRange === ""
  ) {
    updateWeeklyOffDates();
  }
};

const saveHoliday = () => {
  const validationErrors = validateHoliday();
  if (Object.values(validationErrors).some((error) => error)) {
    toast.error(
      "Invalid fields, check if all are filled in and values are correct."
    );
    return;
  }

  createHoliday();
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
    auto: true,
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
    onSuccess(data) {
      toast.success("Holiday list created");
      isDirty.value = false;
      router.push({
        name: "EditBusinessHolidays",
        params: { id: data.name },
        query: router.currentRoute.value.query,
      });
    },
  });
};

watch(
  holidayData,
  (newVal) => {
    if (!initialData.value) return;

    isDirty.value = JSON.stringify(newVal) != initialData.value;
  },
  { deep: true }
);

const confirmLeave = () => {
  return new Promise<boolean>((resolve) => {
    $dialog({
      title: __("Unsaved changes"),
      message: __(
        "Are you sure you want to leave? Unsaved changes will be lost."
      ),
      actions: [
        {
          label: "Confirm",
          variant: "solid",
          onClick: (close: Function) => {
            resolve(true);
            close();
          },
        },
        {
          label: "Cancel",
          variant: "ghost",
          onClick: (close: Function) => {
            resolve(false);
            close();
          },
        },
      ],
    });
  });
};

onBeforeRouteLeave(async (to, from, next) => {
  if (isDirty.value) {
    const confirmed = await confirmLeave();
    if (confirmed) {
      next();
    } else {
      next(false);
    }
  } else {
    next();
  }
});
</script>
