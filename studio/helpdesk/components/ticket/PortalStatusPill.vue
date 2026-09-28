<template>
  <span class="inline-flex min-w-0 items-center gap-1.5">
    <span
      :class="['size-2 shrink-0 rounded-full', STATUS_DOT_CLASSES[color]]"
    />
    <span class="whitespace-nowrap text-p-sm text-ink-gray-8">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
import { STATUS_DOT_CLASSES, type StatusColor } from "@app/stores/ticketMeta";

withDefaults(defineProps<{ label?: string; color?: StatusColor }>(), {
  label: "",
  color: "gray",
});
</script>
