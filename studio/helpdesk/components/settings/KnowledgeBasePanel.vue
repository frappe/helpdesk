<template>
  <!-- The page under the dialog reads pins from the session, as after Save. -->
  <KnowledgeBaseForm
    v-model:tab="knowledgeBaseTab"
    @pins-saved="session.reloadSession()"
  />
</template>

<script setup lang="ts">
// Studio only finds custom blocks under the app folder.
import KnowledgeBaseForm from "@helpdesk/shared/settings/KnowledgeBaseForm.vue";
import { useSession } from "@app/stores/session";
import { knowledgeBaseTab } from "@app/stores/settings";

const session = useSession();
</script>
