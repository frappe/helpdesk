<template>
  <span class="inline-flex min-w-0 items-center gap-1.5">
    <span
      :class="[
        'shrink-0 rounded-full',
        size === 'sm' ? 'size-[7px]' : 'size-2',
        STATUS_DOT_CLASSES[color],
      ]"
    />
    <!-- `sm` is the list's: it truncates, in the row's own text colour. -->
    <span
      :class="
        size === 'sm'
          ? 'flex-1 truncate text-base'
          : 'whitespace-nowrap text-p-sm text-ink-gray-8'
      "
    >
      {{ label }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { STATUS_DOT_CLASSES, type StatusColor } from "@app/stores/ticketMeta";

withDefaults(
  defineProps<{ label?: string; color?: StatusColor; size?: "sm" | "md" }>(),
  {
    label: "",
    color: "gray",
    size: "md",
  }
);
</script>
