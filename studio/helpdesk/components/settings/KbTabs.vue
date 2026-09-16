<template>
  <TabsRoot v-model="active">
    <TabsList class="relative flex items-center gap-6 border-b border-outline-gray-1">
      <!-- translate-y-px drops the bar onto the rail rather than above it. -->
      <TabsIndicator
        class="absolute bottom-0 left-0 h-px w-[var(--reka-tabs-indicator-size)] translate-x-[var(--reka-tabs-indicator-position)] translate-y-px transition-[width,transform] duration-300 ease-out motion-reduce:transition-none"
      >
        <div class="size-full bg-[var(--ink-gray-8)]" />
      </TabsIndicator>
      <!-- One weight for every tab: the indicator is sized from the tab's width. -->
      <TabsTrigger
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        class="inline-flex h-7 cursor-pointer appearance-none items-center whitespace-nowrap border-0 bg-transparent p-0 text-p-base font-medium text-ink-gray-5 transition-colors duration-150 ease-out hover:text-ink-gray-7 data-[state=active]:text-ink-gray-8 motion-reduce:transition-none"
      >
        {{ option.label }}
      </TabsTrigger>
    </TabsList>
  </TabsRoot>
</template>

<script setup lang="ts">
// `TabsIndicator` is one element reka positions from the active tab, so the bar travels
// instead of cutting. Not frappe-ui's `Tabs`: that owns the panels and keys them by index.
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
