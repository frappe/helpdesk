<template>
  <SettingsLayoutBase
    :title="__('Knowledge Base')"
    :description="__('Manage how the knowledge base appears to customers.')"
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
