<template>
  <div
    class="px-4.5 flex cursor-pointer flex-col justify-between rounded-md border py-4 hover:border-gray-400"
    :style="{
      height: '134px',
    }"
  >
    <span>
      <div class="mb-1 text-lg font-medium text-gray-900">{{ title }}</div>
      <div class="line-clamp-3 text-base text-gray-700">
        {{ description }}
      </div>
    </span>
    <div class="text-base text-gray-600">
      {{ articleCount ? articleCount : "No" }}
      {{ articleCount > 1 ? "articles" : "article" }}
    </div>
  </div>
</template>
<script setup lang="ts">
defineProps({
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    required: false,
    default: "",
  },
  articleCount: {
    type: Number,
    required: false,
    default: 0,
    validator: (count: number) => count >= 0,
  },
});
</script>
