<template>
  <KnowledgeBaseForm @saved="session.reloadSession()" />
</template>

<script setup lang="ts">
// Studio finds custom blocks only under the app folder, so the desk's page reaches the block tree through this.
import KnowledgeBaseForm from "@helpdesk/shared/settings/KnowledgeBaseForm.vue";
import { useSession } from "@app/stores/session";

const session = useSession();
</script>
