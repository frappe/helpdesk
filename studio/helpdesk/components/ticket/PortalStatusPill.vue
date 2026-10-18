<template>
  <span class="inline-flex min-w-0 items-center gap-1.5">
    <span
      :class="[
        'shrink-0 rounded-full bg-current',
        size === 'sm' ? 'size-[7px]' : 'size-2',
        statusDotClass(color),
      ]"
    />
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
import { statusDotClass } from "@helpdesk/shared/ticketStatus";

withDefaults(
  defineProps<{ label?: string; color?: string; size?: "sm" | "md" }>(),
  {
    label: "",
    color: "Gray",
    size: "md",
  }
);
</script>
