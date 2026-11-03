<template>
  <span
    class="flex items-center gap-2"
    :aria-label="__('{0} published, {1} other', [published, total - published])"
  >
    <svg viewBox="0 0 16 16" class="size-4 -rotate-90" aria-hidden="true">
      <circle
        cx="8"
        cy="8"
        r="6"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        class="text-ink-amber-3"
      />
      <circle
        cx="8"
        cy="8"
        r="6"
        fill="none"
        stroke="currentColor"
        stroke-width="2.5"
        stroke-linecap="round"
        class="text-ink-green-5"
        :stroke-dasharray="RING"
        :stroke-dashoffset="RING * (1 - published / total)"
      />
    </svg>
    <span class="text-sm tabular-nums text-ink-gray-7">
      {{
        published < total
          ? __("{0} of {1} live", [published, total])
          : __("All live")
      }}
    </span>
  </span>
</template>

<script setup lang="ts">
import { __ } from "@/translation";

// Share of published articles, as a ring.
defineProps<{ published: number; total: number }>();

const RING = 2 * Math.PI * 6;
</script>
