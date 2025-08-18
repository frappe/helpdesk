<template>
  <div class="flex items-center justify-between">
    <div class="flex flex-col gap-1">
      <div class="text-lg font-semibold text-ink-gray-8">
        Work schedule and holidays
      </div>
      <div class="text-p-sm text-ink-gray-6 max-w-lg">
        Set working days, hours, and holidays by selecting a predefined schedule
        or creating a new one.
      </div>
    </div>
    <NestedPopover>
      <template #target="{ open }">
        <Button
          class="text-sm"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
          :label="slaData.holiday_list"
        />
      </template>
      <template #body>
        <div
          class="my-2 p-1 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
        >
          <div>
            <div
              v-for="holiday in holidayListData.data"
              :key="holiday.name"
              class="flex items-center justify-between gap-4 rounded px-2 py-1.5 text-base text-ink-gray-8 cursor-pointer hover:bg-surface-gray-2"
              @click="slaData.holiday_list = holiday.name"
            >
              <div class="flex items-center gap-2 w-full">
                <input
                  name="holiday_list"
                  :checked="holiday.name === slaData.holiday_list"
                  type="radio"
                />
                <div class="select-none">{{ holiday.holiday_list_name }}</div>
              </div>
              <div class="flex cursor-pointer items-center gap-1">
                <Button
                  variant="ghost"
                  @click.stop="editHolidayList(holiday)"
                  icon="edit"
                />
              </div>
            </div>
            <div
              class="mt-1.5 flex flex-col gap-1 border-t border-outline-gray-modals pt-1.5"
            >
              <Button
                class="w-full !justify-start !text-ink-gray-5"
                variant="ghost"
                label="Create new business holiday"
                @click="createNewHolidayList()"
                icon-left="plus"
              />
            </div>
          </div>
        </div>
      </template>
    </NestedPopover>
  </div>
  <div class="mt-5">
    <SlaWorkDaysList />
  </div>
</template>

<script setup lang="ts">
import { NestedPopover, Button, createListResource } from "frappe-ui";
import SlaWorkDaysList from "./SlaWorkDaysList.vue";
import { setActiveSettingsTab } from "../settingsModal";
import {
  holidayListActiveScreen,
  resetHolidayData,
} from "@/stores/holidayList";
import { watchDebounced } from "@vueuse/core";
import { slaData, validateSlaData } from "@/stores/sla";

const createNewHolidayList = () => {
  setActiveSettingsTab("Business Holidays");
  holidayListActiveScreen.value = {
    screen: "view",
    data: null,
    previousScreen: {
      screen: "view",
      data: slaData.value.name,
    },
  };
  resetHolidayData();
};

const editHolidayList = (data: any) => {
  setActiveSettingsTab("Business Holidays");
  holidayListActiveScreen.value = {
    screen: "view",
    data: data,
    previousScreen: {
      screen: "view",
      data: slaData.value.name,
    },
  };
};

const holidayListData = createListResource({
  doctype: "HD Service Holiday List",
  fields: ["name", "holiday_list_name"],
  auto: true,
});

watchDebounced(
  slaData.value.support_and_resolution,
  () => {
    validateSlaData("support_and_resolution");
  },
  { debounce: 300 }
);
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
