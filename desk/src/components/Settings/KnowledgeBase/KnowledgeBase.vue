<template>
  <SettingsLayoutBase
    :description="
      __('Manage who can read your knowledge base and how it looks.')
    "
  >
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-md-semibold text-ink-gray-8">
          {{ __("Knowledge Base") }}
        </h1>
        <UnsavedBadge :show="isDirty" />
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <div v-if="isDirty" class="flex items-center gap-2">
          <Button
            v-if="canPreview"
            icon-left="lucide-external-link"
            :label="__('Preview')"
            @click="preview"
          />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="save"
          />
        </div>
      </Transition>
    </template>
    <template #content>
      <KnowledgeBaseForm />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import { __ } from "@/translation";
import KnowledgeBaseForm from "@helpdesk/shared/settings/KnowledgeBaseForm.vue";
import { useKnowledgeBaseDraft } from "@helpdesk/shared/settings/knowledgeBaseDraft.ts";
import { Button } from "frappe-ui";

const { isDirty, canPreview, saving, save, preview } = useKnowledgeBaseDraft();
</script>
