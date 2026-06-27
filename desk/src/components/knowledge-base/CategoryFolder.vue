<template>
  <router-link
    class="flex flex-col gap-2 rounded-lg border p-3 border-outline-elevation-2 cursor-pointer hover:shadow-xl"
    :to="{
      name: 'Articles',
      params: {
        categoryId: category.name,
      },
    }"
  >
    <div>
      <span class="lucide-folder h-6 w-6 text-ink-gray-4 -ms-[2px]" />
    </div>
    <div class="gap-1 flex flex-col">
      <p class="text-base-medium text-ink-gray-8 truncate">
        {{ category?.category_name }}
      </p>
      <span class="truncate text-xs md:text-sm text-ink-gray-5">
        {{ category?.article_count }}
        {{ category?.article_count % 2 === 1 ? "article" : "articles" }}
      </span>
    </div>
  </router-link>
</template>

<script setup lang="ts">
const props = defineProps({
  category: {
    required: true,
    type: Object,
  },
});
</script>
