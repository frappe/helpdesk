<template>
  <div class="flex flex-col gap-2">
    <div class="text-lg font-medium">Work Schedule & Holidays</div>
    <div class="flex justify-between">
      <div class="text-sm text-gray-600">
        Set working days, hours, and holidays by selecting a predefined schedule
        or creating a new one.
      </div>
      <NestedPopover>
        <template #target="{ isOpen }">
          <Button class="text-sm">
            {{ holidayList }}
            <template #suffix>
              <FeatherIcon
                :name="isOpen ? 'chevron-up' : 'chevron-down'"
                class="h-4 text-gray-600"
              />
            </template>
          </Button>
        </template>
        <template #body="{ close }">
          <div
            class="my-2 p-1 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
          >
            <div>
              <div
                v-for="holiday in holidayListData.data"
                :key="holiday.name"
                class="flex items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-ink-gray-8 hover:bg-surface-gray-2"
              >
                <div
                  class="flex items-center gap-2 cursor-pointer"
                  @click="holidayList = holiday.name"
                >
                  <input
                    name="holiday_list"
                    :checked="holiday.name === holidayList"
                    type="radio"
                  />
                  <div>{{ holiday.holiday_list_name }}</div>
                </div>
                <div class="flex cursor-pointer items-center gap-1">
                  <Button variant="ghost" class="!h-5 w-5 !p-1">
                    <FeatherIcon name="edit" class="h-3.5" />
                  </Button>
                </div>
              </div>
              <div
                class="mt-1.5 flex flex-col gap-1 border-t border-outline-gray-modals pt-1.5"
              >
                <Button
                  class="w-full !justify-start !text-ink-gray-5"
                  variant="ghost"
                  label="Create new holiday list"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
                <Button
                  class="w-full !justify-start !text-ink-gray-5"
                  variant="ghost"
                  label="Reset to Default"
                >
                  <template #prefix>
                    <ReloadIcon class="h-4" />
                  </template>
                </Button>
              </div>
            </div>
          </div>
        </template>
      </NestedPopover>
    </div>
    <div class="mt-4">
      <SlaWorkDaysList :workDaysList="props.workDaysList" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { createResource } from "frappe-ui";
import SlaWorkDaysList from "./SlaWorkDaysList.vue";

const holidayList = defineModel<string>();

const props = defineProps({
  workDaysList: {
    type: Array<any>,
    required: true,
  },
});

const holidayListData = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Service Holiday List",
    fields: ["*"],
    parent: "HD Service Level Agreement",
  },
  auto: true,
  onSuccess: (data) => {
    console.log("holidayList", data);
  },
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
