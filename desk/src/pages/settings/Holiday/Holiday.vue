<template>
  <SettingsHeader :routes="routes" />
  <div
    class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
  >
    <div
      v-if="holidayList.list.loading && !holidayList.list.data"
      class="flex items-center justify-center mt-12"
    >
      <LoadingIndicator class="w-4" />
    </div>
    <div v-else>
      <div
        v-if="!holidayList.list.loading && !holidayList.list.data?.length"
        class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
      >
        <div class="p-4 size-16 rounded-full bg-surface-gray-1">
          <Briefcase class="size-8 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-lg font-medium text-ink-gray-6">
            No Holiday list found
          </div>
          <div class="text-base text-ink-gray-5 max-w-60 text-center">
            Add your first Holiday list to get started.
          </div>
        </div>
        <Button
          label="Add Holiday"
          variant="outline"
          icon-left="plus"
          @click="goToNew()"
        />
      </div>
      <div v-else>
        <div class="flex text-sm text-gray-600">
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
    <div
      v-if="holidayList.list.data?.length"
      class="bg-white py-4 lg:py-8 lg:pb-6 sticky top-0"
    >
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
import Briefcase from "~icons/lucide/briefcase";

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
