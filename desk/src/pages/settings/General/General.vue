<template>
  <SettingsHeader :routes="routes" />
  <div v-if="!settingsData.doc" class="flex items-center justify-center mt-12">
    <LoadingIndicator class="w-4" />
  </div>
  <div v-else class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
    <Branding />
    <hr class="my-8" />
    <TicketSettings />
    <hr class="my-8" />
    <WorkflowKnowledgebaseSettings />
    <!-- <hr class="my-8" />
    <SlaSettings /> -->
  </div>
</template>

<script setup lang="ts">
import { computed, provide } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import TicketSettings from "./components/TicketSettings.vue";
import WorkflowKnowledgebaseSettings from "./components/WorkflowKnowledgebaseSettings.vue";
import { createDocumentResource, LoadingIndicator, toast } from "frappe-ui";
import Branding from "./components/Branding.vue";

const settingsData = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
  auto: true,
  setValue: {
    onSuccess() {
      toast.success("Settings updated");
    },
  },
});

provide("settingsData", settingsData);

const routes = computed(() => [
  {
    label: "General",
    to: "/settings/general",
  },
]);
</script>
