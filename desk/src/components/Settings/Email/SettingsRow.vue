<template>
  <div class="flex items-start justify-between gap-4">
    <div class="flex flex-col">
      <div class="text-p-base text-ink-gray-8">{{ label }}</div>
      <p v-if="description" class="text-p-sm text-ink-gray-5 max-w-md">
        {{ description }}
      </p>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  label: string;
  description?: string;
}

withDefaults(defineProps<Props>(), { description: "" });
</script>
