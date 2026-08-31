<template>
  <TabsRoot v-model="active">
    <TabsList class="kb-tabs">
      <TabsIndicator class="kb-tabs__indicator">
        <div class="kb-tabs__bar" />
      </TabsIndicator>
      <TabsTrigger
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        class="kb-tabs__tab"
      >
        {{ option.label }}
      </TabsTrigger>
    </TabsList>
  </TabsRoot>
</template>

<script setup lang="ts">
// Underline tabs, built on the same reka-ui primitives frappe-ui's own `Tabs` uses.
//
// It was `TabButtons type="underline"` before, which draws the underline as a static
// `::after` on whichever tab is active — so switching tabs made the bar disappear here
// and reappear there. `TabsIndicator` is one element that reka positions from the active
// tab's own box, handing over its width and offset as CSS variables, so the bar can
// travel between tabs instead of cutting.
//
// Not frappe-ui's `Tabs` itself: that one owns the panels too, keys its model by tab
// index, and carries page-level padding on the strip. Here the panels are separate Studio
// blocks and the model is the tab's own name.
import { computed } from "vue";
import { TabsIndicator, TabsList, TabsRoot, TabsTrigger } from "reka-ui";

const props = defineProps<{
  modelValue?: string;
  options?: { label: string; value: string }[];
}>();
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const active = computed({
  get: () => props.modelValue,
  set: (value) => emit("update:modelValue", value),
});
</script>

<style scoped>
/* Plain CSS: this app sits outside the bench's Tailwind content globs, so only
   utilities the rest of the bundle already uses are safe here. */
.kb-tabs {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid var(--outline-gray-1);
}

.kb-tabs__indicator {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 1px;
  width: var(--reka-tabs-indicator-size);
  /* A pixel down, so the bar lands on the rail rather than above it. */
  transform: translateX(var(--reka-tabs-indicator-position)) translateY(1px);
  transition: width 300ms ease-out, transform 300ms ease-out;
}

.kb-tabs__bar {
  width: 100%;
  height: 100%;
  background: var(--ink-gray-8);
}

.kb-tabs__tab {
  appearance: none;
  border: 0;
  background: none;
  padding: 0;
  height: 28px;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  white-space: nowrap;
  font-size: 14px;
  /* One weight for every tab. Bolding the active one would change its width, and the
     indicator is sized from that width — the bar would resize under itself mid-travel. */
  font-weight: 500;
  color: var(--ink-gray-5);
  transition: color 150ms ease-out;
}

.kb-tabs__tab:hover {
  color: var(--ink-gray-7);
}

.kb-tabs__tab[data-state="active"] {
  color: var(--ink-gray-8);
}

@media (prefers-reduced-motion: reduce) {
  .kb-tabs__indicator,
  .kb-tabs__tab {
    transition: none;
  }
}
</style>
