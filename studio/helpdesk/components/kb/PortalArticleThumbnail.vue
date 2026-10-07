<template>
  <img
    v-if="src && src !== failedSrc"
    :src="src"
    alt=""
    loading="lazy"
    class="size-9 shrink-0 rounded-5 object-cover"
    @error="failedSrc = src"
  />
  <span
    v-else
    class="flex size-9 shrink-0 items-center justify-center rounded-5 text-ink-gray-6"
  >
    <svg
      viewBox="0 0 16 16"
      fill="currentColor"
      aria-hidden="true"
      class="size-[18px]"
    >
      <path :d="DOCUMENT_GLYPH" />
    </svg>
  </span>
</template>

<script setup lang="ts">
import { ref } from "vue";

const DOCUMENT_GLYPH =
  "M11 1C12.6569 1 14 2.34315 14 4V12.5C14 13.8807 12.8807 15 11.5 15H4.5C3.11929 15 2 13.8807 2 12.5V3.5C2 2.11929 3.11929 1 4.5 1H11ZM4.5 2C3.67157 2 3 2.67157 3 3.5V12.5C3 13.3284 3.67157 14 4.5 14H11.5C12.3284 14 13 13.3284 13 12.5V4C13 2.89543 12.1046 2 11 2H4.5ZM10.75 10.5C11.0261 10.5 11.25 10.7239 11.25 11C11.25 11.2761 11.0261 11.5 10.75 11.5H5.25C4.97386 11.5 4.75 11.2761 4.75 11C4.75 10.7239 4.97386 10.5 5.25 10.5H10.75ZM10.75 7.5C11.0261 7.5 11.25 7.72386 11.25 8C11.25 8.27614 11.0261 8.5 10.75 8.5H5.25C4.97386 8.5 4.75 8.27614 4.75 8C4.75 7.72386 4.97386 7.5 5.25 7.5H10.75ZM10.75 4.5C11.0261 4.5 11.25 4.72386 11.25 5C11.25 5.27614 11.0261 5.5 10.75 5.5H5.25C4.97386 5.5 4.75 5.27614 4.75 5C4.75 4.72386 4.97386 4.5 5.25 4.5H10.75Z";

withDefaults(defineProps<{ src?: string | null }>(), { src: null });

// Rows are reused across queries, so a dead image must not stick to the next one.
const failedSrc = ref<string | null>(null);
</script>
