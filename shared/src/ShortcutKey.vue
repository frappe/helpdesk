<template>
  <span class="inline-flex items-center gap-1">
    <kbd
      v-for="(key, index) in keyList"
      :key="index"
      class="flex items-center justify-center border border-outline-gray-2 bg-surface-base pt-px text-ink-gray-5"
      :class="
        size === 'sm'
          ? 'h-4 min-w-4 rounded-[4px] px-0.5 text-[10px]'
          : 'h-5 min-w-5 rounded-[5px] px-1 text-xs'
      "
    >
      {{ key }}
    </kbd>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

/** Space-separated keys render as separate caps: "L A" -> [L][A]. */
const props = defineProps<{ keys: string; size?: "sm" }>();

const keyList = computed(() => props.keys.trim().split(/\s+/));
</script>
