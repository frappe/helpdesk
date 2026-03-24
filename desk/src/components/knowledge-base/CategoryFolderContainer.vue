<template>
  <div
    class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5"
    v-if="!categories.loading && categories.data?.length > 0"
  >
    <CategoryFolder
      v-for="category in categories.data"
      :key="category.name"
      :category="category"
    />
  </div>
  <div
    v-if="!categories.loading && categories.data?.length < 1"
    class="absolute left-0 top-0 w-full h-screen flex flex-col items-center justify-center"
  >
    <EmptyState
      :title="__('No categories available')"
      :description="__('There are no categories published at the moment.')"
      :icon="iconVNode"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, h } from "vue";
import { categories } from "@/stores/knowledgeBase";
import CategoryFolder from "./CategoryFolder.vue";
import EmptyState from "../EmptyState.vue";
import LucideBookOpen from "~icons/lucide/book-open";
const iconVNode = h(LucideBookOpen);

onMounted(() => {
  categories.fetch();
});
</script>
