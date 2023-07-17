<template>
  <div class="flex flex-col">
    <PageTitle title="Knowledge base" />
    <div class="flex grow border-t">
      <KnowledgeBaseSidebar />
      <RouterView v-slot="{ Component }">
        <component :is="Component" v-if="Component" />
        <KnowledgeBaseCategory
          v-else-if="activeCategory"
          :key="activeCategory"
          :category-id="activeCategory"
        />
        <div v-else class="m-auto text-base text-gray-900">
          &longleftarrow; Select a category
        </div>
      </RouterView>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia";
import PageTitle from "@/components/PageTitle.vue";
import KnowledgeBaseSidebar from "./KnowledgeBaseSidebar.vue";
import KnowledgeBaseCategory from "./KnowledgeBaseCategory.vue";
import { useKnowledgeBaseStore } from "./data";

const { activeCategory } = storeToRefs(useKnowledgeBaseStore());
</script>
