<template>
  <div
    class="grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none"
    :class="open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
    :inert="!open"
  >
    <div class="min-h-0 overflow-hidden">
      <slot v-if="rendered" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

// `lazy`: unrender folded content after the close animation.
const props = defineProps<{ open: boolean; lazy?: boolean }>();

const CLOSE_DURATION = 200;
const rendered = ref(!props.lazy || props.open);
let closing: ReturnType<typeof setTimeout> | undefined;

watch(
  () => props.open,
  (open) => {
    if (!props.lazy) return;
    clearTimeout(closing);
    if (open) rendered.value = true;
    else closing = setTimeout(() => (rendered.value = false), CLOSE_DURATION);
  }
);
</script>
