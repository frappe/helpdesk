<template>
  <div class="flex flex-col h-full w-full pb-8">
    <div class="px-10 py-8">
      <div class="flex items-start justify-between">
        <div class="flex flex-col gap-1">
          <slot name="title">
            <h1 class="text-lg font-semibold text-ink-gray-8">
              {{ title }}
            </h1>
          </slot>
          <slot
            name="description"
            v-if="Boolean($slots['description']) || Boolean(description)"
          >
            <p class="text-p-sm text-gray-700 max-w-md text-ink-gray-6">
              {{ description }}
            </p>
          </slot>
        </div>
        <slot name="header-actions" v-if="Boolean($slots['header-actions'])" />
      </div>
      <div class="mt-6" v-if="Boolean($slots['header-bottom'])">
        <slot name="header-bottom" />
      </div>
    </div>
    <div class="px-10 pb-8 overflow-y-auto h-full flex flex-col">
      <slot name="content" />
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  title: {
    type: String,
  },
  description: {
    type: String,
  },
});
</script>
