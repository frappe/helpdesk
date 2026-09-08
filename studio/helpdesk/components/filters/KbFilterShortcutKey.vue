<!-- Ported from the agent portal's own control: `@/` does not resolve in this app. -->
<template>
  <span class="inline-flex items-center gap-1">
    <kbd
      v-for="(key, index) in keyList"
      :key="index"
      class="flex h-5 min-w-5 items-center justify-center rounded-[5px] border border-outline-gray-2 bg-surface-base px-1 pt-px text-xs text-ink-gray-5"
    >
      {{ key }}
    </kbd>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

/** Space-separated keys render as separate caps: "L A" -> [L][A]. */
const props = defineProps<{ keys: string }>();

const keyList = computed(() => props.keys.trim().split(/\s+/));
</script>
