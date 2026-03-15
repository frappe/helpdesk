<template>
  <router-link
    class="flex flex-col gap-2 rounded-lg border p-3 border-outline-gray-1 cursor-pointer hover:shadow-xl"
    :to="{
      name: 'Articles',
      params: {
        categoryId: category.name,
      },
    }"
  >
    <div>
      <FeatherIcon name="folder" class="h-6 w-6 text-ink-gray-3 -ml-[2px]" />
    </div>
    <div class="gap-1 flex flex-col">
      <p class="text-base font-medium text-ink-gray-8 truncate">
        {{ category.category_name }}
      </p>
      <span class="truncate text-xs md:text-sm text-ink-gray-4">
        {{ category.article_count }} articles
      </span>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { FeatherIcon } from "frappe-ui";
const props = defineProps({
  category: {
    required: true,
    type: Object,
  },
});
</script>
