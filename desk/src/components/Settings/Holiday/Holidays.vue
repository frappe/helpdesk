<template>
  <SettingsLayoutBase
    :title="__('Business Holidays')"
    :description="
      __(
        'Set your team’s working days, hours, and holidays using a template or custom schedule.'
      )
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="lucide-plus"
      />
    </template>
    <template
      v-if="holidayList.data?.length > 9 || holidaySearchRef.length"
      #header-bottom
    >
      <div class="relative">
        <TextInput
          :model-value="holidaySearchRef"
          @update:model-value="holidaySearchRef = $event"
          :placeholder="__('Search')"
          type="text"
          class="focus:ring-0 border-outline-gray-2"
          :debounce="300"
        >
          <template #prefix>
            <LucideSearch class="size-4" />
          </template>
        </TextInput>
        <Button
          v-if="holidaySearchRef"
          icon="lucide-x"
          variant="ghost"
          @click="holidaySearchRef = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
        />
      </div>
    </template>
    <template #content>
      <HolidayList />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import {
  holidayListActiveScreen,
  resetHolidayData,
} from "@/stores/holidayList";
import HolidayList from "./HolidayList.vue";
import { inject, Ref, ref, watch } from "vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { HolidayListResourceSymbol } from "@/types";

const holidayList = inject(HolidayListResourceSymbol);
const holidaySearchRef = inject<Ref<string>>("holidaySearchRef");

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
