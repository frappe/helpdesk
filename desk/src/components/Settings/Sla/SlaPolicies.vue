<template>
  <div class="px-10 py-8">
    <SettingsLayoutHeader>
      <template #title>
        <h1 class="text-lg font-semibold text-ink-gray-8">
          Service Level Agreements (SLAs)
        </h1>
      </template>
      <template #description>
        <p class="text-p-sm max-w-md text-ink-gray-6">
          SLAs align your team and customers with defined timelines for a
          reliable experience.
          <a
            href="https://docs.frappe.io/helpdesk/service-level-agreement"
            target="_blank"
            class="underline"
            >Learn more about SLA
          </a>
        </p>
      </template>
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
  <div class="px-10 pb-8 overflow-y-auto">
    <SlaPolicyList />
  </div>
</template>

<script setup lang="ts">
import { resetSlaData, slaActiveScreen } from "@/stores/sla";
import { Button } from "frappe-ui";
import SlaPolicyList from "./SlaPolicyList.vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";

const goToNew = () => {
  resetSlaData();
  slaActiveScreen.value = {
    screen: "view",
    data: null,
    fetchData: true,
  };
};
</script>
