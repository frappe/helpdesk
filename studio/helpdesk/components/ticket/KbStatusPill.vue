<template>
  <span class="inline-flex min-w-0 items-center gap-1.5">
    <span class="size-2 shrink-0 rounded-full" :style="{ background: color }" />
    <span class="whitespace-nowrap text-p-sm text-ink-gray-8">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
// Where the ticket stands, in the colour HD Ticket Status gives it — the same dot the
// portal's ticket list draws, so one ticket reads the same in both places. The colour
// arrives resolved (`statusMeta` maps it to an espresso token), inline because it is a
// runtime value.

withDefaults(defineProps<{ label?: string; color?: string }>(), {
  label: "",
  color: "var(--ink-gray-6)",
});
</script>
