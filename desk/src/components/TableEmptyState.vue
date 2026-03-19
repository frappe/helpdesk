<template>
  <div
    class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
  >
    <div
      class="bg-surface-white/80 backdrop-blur-md space-y-1.5 w-64 p-4 rounded border border-white/20 shadow-2xl"
    >
      <div class="text-ink-gray-9 font-semibold text-center text-base">
        {{ title }}
      </div>
      <div class="text-ink-gray-5 text-center text-p-sm">
        {{ description }}
      </div>
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
    required: true,
  },
});
</script>
