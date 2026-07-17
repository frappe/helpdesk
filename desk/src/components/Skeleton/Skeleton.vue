<template>
  <div
    v-if="loading && hasContent"
    ref="root"
    class="skeleton-mask animate-pulse"
    aria-hidden="true"
    inert
    v-bind="$attrs"
  >
    <slot />
  </div>
  <div
    v-else-if="loading"
    class="animate-pulse bg-surface-gray-2"
    :class="variantClasses[variant]"
    :style="{ width, height }"
    aria-hidden="true"
    v-bind="$attrs"
  />
  <slot v-else />
</template>

<script setup lang="ts">
import { computed, onMounted, onUpdated, ref, useSlots } from "vue";
import type { SkeletonProps } from "./types";

defineOptions({ inheritAttrs: false });

const props = withDefaults(defineProps<SkeletonProps>(), {
  loading: true,
  variant: "line",
});

const slots = useSlots();
const root = ref<HTMLElement | null>(null);

const hasContent = computed(() => Boolean(slots.default));

const variantClasses = {
  line: "h-4 rounded",
  circle: "rounded-full",
  box: "rounded-md",
};

// Elements that always become a gray bone, without descending further.
const boneTags = new Set([
  "IMG",
  "SVG",
  "BUTTON",
  "INPUT",
  "TEXTAREA",
  "SELECT",
  "VIDEO",
  "CANVAS",
]);

function markBones(): void {
  if (root.value) {
    for (const child of Array.from(root.value.children)) walk(child);
  }
}

function walk(element: Element): void {
  if (isBone(element)) {
    element.classList.add("skeleton-bone");
    return;
  }
  for (const child of Array.from(element.children)) walk(child);
}

function isBone(element: Element): boolean {
  if (boneTags.has(element.tagName.toUpperCase())) return true;
  return hasDirectText(element);
}

function hasDirectText(element: Element): boolean {
  return Array.from(element.childNodes).some(
    (node) => node.nodeType === Node.TEXT_NODE && node.textContent?.trim()
  );
}

onMounted(markBones);
onUpdated(markBones);
</script>

<style scoped>
.skeleton-mask {
  pointer-events: none;
  user-select: none;
}
.skeleton-mask :deep(*) {
  color: transparent !important;
}
.skeleton-mask :deep(.skeleton-bone) {
  background-color: var(--surface-gray-2) !important;
  background-image: none !important;
  border-radius: 0.25rem;
  box-shadow: none !important;
}
.skeleton-mask :deep(.skeleton-bone *) {
  visibility: hidden !important;
}
</style>
