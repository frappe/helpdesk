<template>
  <div class="flex items-center justify-between p-6">
    <slot name="title">
      <div v-if="title" class="text-2xl font-semibold text-gray-900">
        {{ title }}
      </div>
    </slot>
    <slot name="right" />
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
