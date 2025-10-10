<template>
  <div class="px-10 py-8 sticky top-0">
    <SettingsLayoutHeader
      title="Business Holidays"
      description="Set your team’s working days, hours, and holidays using a template or custom schedule."
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
      <template
        v-if="holidayList.data?.length > 9 || holidaySearchRef.length"
        #bottom-section
      >
        <div class="relative">
          <Input
            v-model="holidaySearchRef"
            @input="holidaySearchRef = $event"
            placeholder="Search"
            type="text"
            class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
            icon-left="search"
            debounce="300"
            inputClass="p-4 pr-12"
          />
          <Button
            v-if="holidaySearchRef"
            icon="x"
            variant="ghost"
            @click="holidaySearchRef = ''"
            class="absolute right-1 top-1/2 -translate-y-1/2"
          />
        </div>
      </template>
    </SettingsLayoutHeader>
  </div>
  <div class="overflow-y-auto pb-8 px-10">
    <HolidayList />
  </div>
</template>

<script setup lang="ts">
import {
  holidayListActiveScreen,
  resetHolidayData,
} from "@/stores/holidayList";
import HolidayList from "./HolidayList.vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import { inject, Ref, ref, watch } from "vue";

const holidayList = inject<any>("holidayList");
const holidaySearchRef = inject<Ref>("holidaySearchRef");

const goToNew = () => {
  resetHolidayData();
  holidayListActiveScreen.value = {
    screen: "view",
    data: null,
  };
};

watch(holidaySearchRef, (newValue) => {
  holidayList.filters = {
    name: ["like", `%${newValue}%`],
  };
  if (!newValue) {
    holidayList.start = 0;
    holidayList.pageLength = 10;
  }
  holidayList.reload();
});
</script>
