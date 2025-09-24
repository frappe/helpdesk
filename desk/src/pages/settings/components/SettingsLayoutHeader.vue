<template>
  <div class="flex items-center justify-between">
    <div class="flex flex-col items-start gap-1 w-full">
      <slot name="title">
        <h1
          v-if="title"
          class="text-xl font-semibold text-ink-gray-9 max-w-[70%] overflow-ellipsis whitespace-nowrap"
        >
          {{ title }}
        </h1>
      </slot>
    </div>
    <slot name="actions" />
  </div>
  <slot name="description">
    <p
      v-if="description"
      class="text-p-base text-gray-700 text-ink-gray-6 mt-1"
    >
      {{ description }}
    </p>
  </slot>
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
