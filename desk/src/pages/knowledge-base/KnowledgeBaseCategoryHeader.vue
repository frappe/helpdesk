<template>
  <div class="space-y-1 px-5 pt-3.5 pb-6">
    <div class="flex items-center justify-between">
      <div class="text-xl font-medium text-gray-900">
        {{ title }}
      </div>
      <slot name="right" />
    </div>
    <div
      class="text-base text-gray-700"
      :style="{
        width: '770px',
      }"
    >
      {{ description }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface P {
  title: string;
  description: string;
}

defineProps<P>();
</script>
