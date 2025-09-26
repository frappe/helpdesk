<template>
  <div>
    <div class="text-lg font-semibold text-gray-900">
      Workflow & Knowledgebase Settings
    </div>
    <div class="mt-6 flex flex-col gap-6">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Skip Email workflow</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Skips automated ticket e-mails. No creation, update, or
            notification e-mails will be sent.</span
          >
        </div>
        <Switch
          :model-value="settingsData.doc.skip_email_workflow"
          @update:model-value="onChange({ skip_email_workflow: $event })"
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Instantly send Email</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Sends immediately, skipping the queue. The e-mail goes out as soon
            as you click Send.</span
          >
        </div>
        <Switch
          :model-value="settingsData.doc.instantly_send_email"
          @update:model-value="onChange({ instantly_send_email: $event })"
        />
      </div>
      <!-- <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Suggest articles in new ticket page</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Show related articles when creating a ticket.</span
          >
        </div>
        <Switch />
      </div> -->
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8"
            >Prefer knowledge base</span
          >
          <span class="text-p-sm text-ink-gray-6"
            >Guide users to articles before tickets.</span
          >
        </div>
        <Switch
          :model-value="settingsData.doc.prefer_knowledge_base"
          @update:model-value="onChange({ prefer_knowledge_base: $event })"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Switch } from "frappe-ui";
import { inject } from "vue";

const settingsData = inject<any>("settingsData");

const onChange = (data) => {
  settingsData.setValue.submit(data);
};
</script>
