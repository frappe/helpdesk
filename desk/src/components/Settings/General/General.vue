<template>
  <div class="pb-8">
    <div class="px-10 py-8">
      <SettingsLayoutHeader
        :title="__('General')"
        :description="__('Manage general settings of your app')"
      />
    </div>
    <div class="px-10 pb-8 overflow-y-auto hide-scrollbar">
      <div v-if="isWebsiteManager">
        <Branding />
      </div>
      <hr class="my-8" v-if="isWebsiteManager && isAdmin" />
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
import { __ } from "@/translation";

const { isWebsiteManager, isAdmin } = useAuthStore();

const settingsData = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
  fields: [
    "brand_logo",
    "favicon",
    "auto_close_after_days",
    "auto_close_status",
    "auto_close_tickets",
    "assign_within_team",
    "do_not_restrict_tickets_without_an_agent_group",
    "restrict_tickets_by_agent_group",
    "update_status_to",
    "auto_update_status",
    "is_feedback_mandatory",
    "allow_anyone_to_create_tickets",
    "default_ticket_type",
    "prefer_knowledge_base",
    "instantly_send_email",
    "skip_email_workflow",
  ],
  auto: true,
  setValue: {
    onSuccess() {
      toast.success(__("Settings updated"));
    },
  },
});

provide("settingsData", settingsData);
</script>
