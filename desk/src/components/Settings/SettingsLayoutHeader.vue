<template>
  <div class="flex items-start justify-between">
    <div class="flex flex-col gap-1">
      <slot name="title">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ title }}
        </h1>
      </slot>
      <slot name="description">
        <p class="text-p-sm text-gray-700 max-w-md text-ink-gray-6">
          {{ description }}
        </p>
      </slot>
    </div>
    <slot name="actions" />
  </div>
  <div class="mt-6" v-if="Boolean($slots['bottom-section'])">
    <slot name="bottom-section" />
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
  },
  description: {
    type: String,
  },
});
</script>
