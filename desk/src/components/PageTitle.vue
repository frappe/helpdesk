<template>
  <header class="border-b px-5 py-2.5">
    <div class="flex items-center justify-between">
      <slot name="title">
        <div v-if="title" class="text-lg font-medium text-gray-900">
          {{ title }}
        </div>
      </slot>
      <slot name="right" />
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
    required: false,
    default: "",
  },
});
</script>
