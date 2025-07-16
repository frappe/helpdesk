<template>
  <div class="px-10 py-8 overflow-y-auto h-full">
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          Service Level Agreements (SLAs)
        </h1>
        <p class="text-sm text-gray-700 max-w-md leading-5 text-ink-gray-6">
          SLAs align your team and customers with defined timelines for a
          reliable experience.
          <a
            href="https://docs.frappe.io/helpdesk/service-level-agreement"
            target="_blank"
            class="text-gray-700 underline"
            >Learn more about SLA
          </a>
        </p>
      </div>
      <Button
        label="New"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </div>
    <div class="mt-6">
      <SlaPolicyList />
    </div>
  </div>
</template>

<script setup lang="ts">
import { resetSlaData, slaActiveScreen } from "@/stores/sla";
import { Button } from "frappe-ui";
import SlaPolicyList from "./SlaPolicyList.vue";

const goToNew = () => {
  resetSlaData();
  slaActiveScreen.value = {
    screen: "view",
    data: null,
    fetchData: true,
  };
};
</script>
