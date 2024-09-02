<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
    </LayoutHeader>
    <div class="flex grow">
      <KnowledgeBaseSidebar />
      <RouterView :key="$route.fullPath" v-slot="{ Component }">
        <component :is="Component" v-if="Component" />
        <EmptyMessage v-else message="Select a category" />
      </RouterView>
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageMeta } from "frappe-ui";
import EmptyMessage from "@/components/EmptyMessage.vue";
import KnowledgeBaseSidebar from "./KnowledgeBaseSidebar.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
