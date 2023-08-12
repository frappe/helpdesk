<template>
  <div class="px-5 py-3">
    <div class="flex items-center justify-between">
      <slot name="title">
        <div v-if="title" class="text-lg font-medium text-gray-900">
          {{ title }}
        </div>
      </slot>
      <slot name="right" />
    </div>
  </div>
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
