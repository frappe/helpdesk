<template>
  <router-link
    class="flex flex-col gap-2 rounded-lg border p-3 border-gray-200 cursor-pointer hover:shadow-xl"
    :to="{
      name: 'Articles',
      params: {
        categoryId: category.name,
      },
    }"
  >
    <Tooltip :text="category.category_name">
      <div>
        <FeatherIcon
          name="folder"
          class="fill-ink-gray-2 h-8 w-8 text-gray-300 -ml-[2px]"
        />
      </div>
      <div class="gap-1 flex flex-col">
        <p class="text-base font-medium text-gray-800 truncate">
          {{ category.category_name }}
        </p>
        <span class="truncate text-xs md:text-sm text-ink-gray-5">
          {{ category.article_count }} articles
        </span>
      </div>
    </Tooltip>
  </router-link>
</template>

<script setup lang="ts">
import { FeatherIcon, Tooltip } from "frappe-ui";
const props = defineProps({
  category: {
    required: true,
    type: Object,
  },
});
</script>

<style scoped></style>
