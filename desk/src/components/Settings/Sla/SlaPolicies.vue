<template>
  <SettingsLayoutBase>
    <template #title>
      <h1 class="text-lg font-semibold text-ink-gray-8">
        {{ __("Service Level Agreements (SLAs)") }}
      </h1>
    </template>
    <template #description>
      <p class="text-p-sm max-w-md text-ink-gray-6">
        {{
          __(
            "SLAs align your team and customers with defined timelines for a reliable experience."
          )
        }}
        <a
          href="https://docs.frappe.io/helpdesk/service-level-agreement"
          target="_blank"
          class="underline"
          >{{ __("Learn more about SLA") }}
        </a>
      </p>
    </template>
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </template>
    <template
      v-if="slaPolicyList.data?.length > 9 || slaSearchQuery.length"
      #header-bottom
    >
      <div class="relative">
        <Input
          :model-value="slaSearchQuery"
          @input="slaSearchQuery = $event"
          :placeholder="__('Search')"
          type="text"
          class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
          icon-left="search"
          debounce="300"
          inputClass="p-4 pr-12"
        />
        <Button
          v-if="slaSearchQuery"
          icon="x"
          variant="ghost"
          @click="slaSearchQuery = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
        />
      </div>
    </template>
    <template #content>
      <SlaPolicyList />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { resetSlaData, slaActiveScreen } from "@/stores/sla";
import { Button } from "frappe-ui";
import SlaPolicyList from "./SlaPolicyList.vue";
import { inject, Ref, watch } from "vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { SlaPolicyListResourceSymbol } from "@/types";
import { __ } from "@/translation";

const slaPolicyList = inject(SlaPolicyListResourceSymbol);
const slaSearchQuery = inject<Ref>("slaSearchQuery");

const goToNew = () => {
  resetSlaData();
  slaActiveScreen.value = {
    screen: "view",
    data: null,
    fetchData: true,
  };
};

watch(slaSearchQuery, (newValue) => {
  slaPolicyList.filters = {
    name: ["like", `%${newValue}%`],
  };
  if (!newValue) {
    slaPolicyList.start = 0;
    slaPolicyList.pageLength = 10;
  }
  slaPolicyList.reload();
});
</script>
