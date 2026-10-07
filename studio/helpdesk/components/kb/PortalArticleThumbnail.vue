<template>
  <img
    v-if="src && src !== failedSrc"
    :src="src"
    alt=""
    loading="lazy"
    class="size-9 shrink-0 rounded-5 border border-outline-gray-2 object-cover"
    @error="failedSrc = src"
  />
  <span
    v-else
    class="flex size-9 shrink-0 items-center justify-center rounded-5 text-ink-gray-6"
  >
    <PortalArticleIcon class="size-[18px]" />
  </span>
</template>

<script setup lang="ts">
import { ref } from "vue";
import PortalArticleIcon from "@app/components/kb/PortalArticleIcon.vue";

withDefaults(defineProps<{ src?: string | null }>(), { src: null });

// Rows are reused across queries, so a dead image must not stick to the next one.
const failedSrc = ref<string | null>(null);
</script>
