<template>
  <div class="flex justify-between px-6 pt-6 pb-2">
    <div class="text-2xl font-semibold text-gray-900">
      {{ title }}
    </div>
    <slot name="right" />
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
    required: true,
  },
});
</script>
