<template>
  <div
    class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
    :style="{
      backgroundImage:
        'radial-gradient(ellipse at center, rgba(255, 255, 255, 1) 30%, rgba(255, 255, 255, 0.8) 30%, rgba(255, 255, 255, 0) 70%)',
    }"
  >
    <div class="space-y-1.5 w-64 p-2 rounded-2xl border-0">
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
