<template>
  <div>
    <div class="text-base font-semibold text-gray-900">
      {{ __("Workflow & knowledge base settings") }}
    </div>
    <div class="mt-6 flex flex-col gap-6">
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Prefer knowledge base")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __("Guide users to articles before tickets.")
          }}</span>
        </div>
        <Switch
          :model-value="settingsData.preferKnowledgeBase"
          @update:model-value="
            (value) => (settingsData.preferKnowledgeBase = value)
          "
        />
      </div>
      <div class="flex items-center justify-between">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">{{
            __("Skip email workflow")
          }}</span>
          <span class="text-p-sm text-ink-gray-6">{{
            __(
              "Disables all email notifications for the ticket - including creation, updates, and alerts."
            )
          }}</span>
        </div>
        <Switch
          :model-value="settingsData.skipEmailWorkflow"
          @update:model-value="
            (value) => (settingsData.skipEmailWorkflow = value)
          "
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { HDSettingsSymbol } from "@/types";
import { Switch } from "frappe-ui";
import { inject } from "vue";
import { __ } from "@/translation";

const settingsData = inject(HDSettingsSymbol);
</script>
