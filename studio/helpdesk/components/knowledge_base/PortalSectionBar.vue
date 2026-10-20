<template>
  <!-- Phone only: shows where you are and opens the article sheet. -->
  <button
    type="button"
    aria-haspopup="dialog"
    :aria-expanded="open"
    class="flex h-10 w-full shrink-0 items-center gap-2 border-y border-outline-gray-1 bg-surface-gray-1 px-4 text-left transition-colors hover:bg-surface-gray-2 active:bg-surface-gray-2 md:hidden"
  >
    <span class="lucide-list size-4 shrink-0 text-ink-gray-6" />
    <span class="shrink-0 text-base text-ink-gray-5">{{ __("Articles") }}</span>
    <span class="shrink-0 text-base text-ink-gray-4">/</span>
    <span class="min-w-0 flex-1 truncate text-base font-medium text-ink-gray-9">
      {{ label }}
    </span>
    <span class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5" />
  </button>
</template>

<script setup lang="ts">
import { __ } from "@helpdesk/shared/translation";

defineProps<{ label?: string; open?: boolean }>();
</script>
