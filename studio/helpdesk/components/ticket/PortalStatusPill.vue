<template>
  <span class="inline-flex min-w-0 items-center gap-1.5">
    <span class="size-2 shrink-0 rounded-full" :style="{ background: color }" />
    <span class="whitespace-nowrap text-p-sm text-ink-gray-8">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
// The colour arrives resolved by `statusMeta`, inline because it is a runtime value.

withDefaults(defineProps<{ label?: string; color?: string }>(), {
  label: "",
  color: "var(--ink-gray-6)",
});
</script>
