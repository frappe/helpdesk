<template>
  <div class="pb-8">
    <div class="px-10 py-8">
      <SettingsLayoutHeader
        title="General"
        description="Manage general settings of your app"
      />
    </div>
    <div class="px-10 pb-8 overflow-y-auto hide-scrollbar">
      <div v-if="isWebsiteManager">
        <Branding />
        <hr class="my-8" />
      </div>
      <div v-if="isAdmin">
        <TicketSettings />
        <hr class="my-8" />
        <WorkflowKnowledgebaseSettings />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createDocumentResource, toast } from "frappe-ui";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import Branding from "./components/Branding.vue";
import TicketSettings from "./components/TicketSettings.vue";
import WorkflowKnowledgebaseSettings from "./components/WorkflowKnowledgebaseSettings.vue";
import { provide } from "vue";
import { useAuthStore } from "@/stores/auth";

const { isWebsiteManager, isAdmin } = useAuthStore();

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
</script>
