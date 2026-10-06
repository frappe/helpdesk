<template>
  <SettingsLayoutBase
    :title="__('Knowledge Base')"
    :description="
      __('Manage who can read your knowledge base and how it looks.')
    "
  >
    <template #content>
      <KnowledgeBaseForm />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import KnowledgeBaseForm from "@helpdesk/shared/settings/KnowledgeBaseForm.vue";
</script>
