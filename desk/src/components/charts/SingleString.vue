<template>
  <div
    class="flex select-none items-center justify-between rounded border px-3 py-2"
  >
    <div class="text-base font-medium text-gray-800">
      {{ title }}
    </div>
    <div class="text-xl">
      {{ value }}
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps({
  title: {
    type: String,
    required: true,
  },
  value: {
    type: String,
    required: true,
  },
});
</script>
