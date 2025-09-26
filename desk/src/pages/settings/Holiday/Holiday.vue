<template>
  <SettingsHeader :routes="routes" />
  <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
    <SettingsLayoutHeader
      :title="__('Business Holidays')"
      :description="
        __(
          'Set your team’s working days, hours, and holidays using a template or custom schedule.'
        )
      "
    >
      <template #actions>
        <Button
          label="New"
          theme="gray"
          variant="solid"
          @click="goToNew()"
          icon-left="plus"
        />
      </template>
    </SettingsLayoutHeader>
    <div
      v-if="holidayList.list.loading && !holidayList.list.data"
      class="flex items-center justify-center mt-12"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else>
      <div
        v-if="holidayList.list.data?.length === 0"
        class="flex flex-col items-center justify-center gap-3 rounded-md border border-gray-200 p-4 mt-7 h-[500px]"
      >
        <div class="text-lg font-medium text-ink-gray-4">
          {{ __("No Business Holiday list found") }}
        </div>
        <Button
          label="Add Business Holiday"
          variant="subtle"
          icon-left="plus"
          @click="goToNew()"
        />
      </div>
      <div v-else>
        <div class="flex text-sm text-gray-600 mt-6">
          <div class="ml-2 text-p-sm">Schedule name</div>
        </div>
        <hr class="mx-2 mt-2" />
        <div>
          <div v-for="holiday in holidayList.list.data" :key="holiday.name">
            <HolidayListItem :data="holiday" />
            <hr class="mx-2" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, provide } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { resetHolidayData } from "@/stores/holidayList";
import { useRouter } from "vue-router";
import { Button, createListResource, LoadingIndicator } from "frappe-ui";
import HolidayListItem from "./components/HolidayListItem.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";

const router = useRouter();

const holidayList = createListResource({
  doctype: "HD Service Holiday List",
  fields: ["name", "description"],
  orderBy: "creation desc",
  start: 0,
  pageLength: 999,
  auto: true,
});

provide("holidayList", holidayList);

const routes = computed(() => [
  {
    label: "Business Holidays",
    route: "/settings/holiday-list",
  },
]);

const goToNew = () => {
  resetHolidayData();
  router.push({
    name: "NewBusinessHolidays",
    params: {
      id: "new",
    },
  });
};
</script>
