<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
      <template #right-header>
        <Button
          label="New article"
          theme="gray"
          variant="solid"
          @click="console.log('a')"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4" />
          </template>
        </Button>
      </template>
    </LayoutHeader>
    <div class="flex grow">
      <KnowledgeBaseSidebar />
    </div>
  </div>
</template>

<script setup lang="ts">
import { usePageMeta } from "frappe-ui";
import EmptyMessage from "@/components/EmptyMessage.vue";

import LayoutHeader from "@/components/LayoutHeader.vue";
import KnowledgeBaseSidebar from "@/components/knowledge-base-v2/KnowledgeBaseSidebar.vue";

usePageMeta(() => {
  return {
    title: "Knowledge base",
  };
});
</script>
