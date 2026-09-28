<template>
  <TabsRoot v-model="active">
    <TabsList
      class="relative flex items-center gap-6 border-b border-outline-gray-1"
    >
      <TabsIndicator
        class="absolute bottom-0 left-0 h-px w-[var(--reka-tabs-indicator-size)] translate-x-[var(--reka-tabs-indicator-position)] translate-y-px transition-[width,transform] duration-300 ease-out motion-reduce:transition-none"
      >
        <div class="size-full bg-[var(--ink-gray-8)]" />
      </TabsIndicator>
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
// reka's TabsIndicator travels between tabs; frappe-ui's Tabs owns the panels.
import { TabsIndicator, TabsList, TabsRoot, TabsTrigger } from "reka-ui";

defineProps<{ options?: { label: string; value: string }[] }>();

const active = defineModel<string>();
</script>
