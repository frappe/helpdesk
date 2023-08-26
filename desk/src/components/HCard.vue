<template>
  <div class="h-full cursor-pointer rounded border p-4 hover:border-gray-400">
    <span>
      <span class="mb-1 block text-lg font-medium text-gray-900">
        {{ title }}
      </span>
      <slot name="description">
        <span class="line-clamp-3 text-base text-gray-700">
          {{ description }}
        </span>
      </slot>
    </span>
    <slot name="bottom" />
  </div>
</template>
<script setup lang="ts">
interface P {
  title: string;
  description?: string;
}

defineProps<P>();
</script>
