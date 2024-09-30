<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="text-lg font-medium text-gray-900">Knowledge base</div>
      </template>
    </LayoutHeader>
    <div class="flex grow">
      <KnowledgeBaseSidebar v-model="currentCategory" />
      <KnowledgeBaseCategoryHandler
        v-if="currentCategory !== 'Explore All Articles'"
        :category-id="currentCategory"
      />
      <div v-else>All</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { LayoutHeader } from "@/components";
import KnowledgeBaseSidebar from "@/components/knowledge-base-v2/KnowledgeBaseSidebar.vue";
import KnowledgeBaseCategoryHandler from "@/components/knowledge-base-v2/KnowledgeBaseCategoryHandler.vue";
const currentCategory = ref("Explore All Articles");
</script>

<style scoped></style>
