<template>
  <span class="flex min-w-0 items-center gap-2">
    <img
      v-if="logo"
      :src="logo"
      alt=""
      aria-hidden="true"
      class="size-6 shrink-0 rounded-2 object-contain"
    />
    <span v-else-if="compact" class="size-6 shrink-0" />
    <span
      v-if="name"
      class="truncate text-base-medium text-ink-gray-9"
      :class="{ 'max-sm:hidden': compact }"
    >
      {{ name }}
    </span>
  </span>
</template>

<script setup lang="ts">
defineProps<{ logo?: string; name?: string; compact?: boolean }>();
</script>
