<template>
  <!-- The box eases to the note's height (0 when there is none) while new text
       rises in. It keeps the last text so a closing note does not go blank. -->
  <div
    class="overflow-hidden transition-[height] duration-300 ease-[cubic-bezier(0.2,0.8,0.2,1)] motion-reduce:transition-none"
    :style="style"
    aria-live="polite"
  >
    <div ref="inner" class="pt-3">
      <Transition
        enter-from-class="translate-y-1 opacity-0 blur-[2px]"
        enter-active-class="transition-[opacity,transform,filter] duration-300 delay-100 ease-out motion-reduce:transition-none"
        leave-active-class="hidden"
      >
        <p
          :key="shown"
          class="text-p-sm text-ink-gray-7 transition-[opacity,transform,filter] duration-150 ease-out motion-reduce:transition-none"
          :class="{ 'translate-y-1 opacity-0 blur-[2px]': !note }"
        >
          {{ shown }}
        </p>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useElementSize } from "@vueuse/core";

const props = defineProps<{ note?: string }>();

const shown = ref(props.note ?? "");
watch(
  () => props.note,
  (note) => note && (shown.value = note)
);

const inner = ref<HTMLElement | null>(null);
const { height } = useElementSize(inner, undefined, { box: "border-box" });
// Unmeasured: natural height, so a note present on open does not grow in.
const style = computed(() => {
  if (!props.note) return { height: "0px" };
  return height.value ? { height: `${height.value}px` } : undefined;
});
</script>
