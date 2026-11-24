<template>
  <span class="flex min-w-0 items-center gap-2">
    <img
      v-if="logo"
      :src="logo"
      alt=""
      aria-hidden="true"
      class="shrink-0"
      :class="logoClass"
    />
    <slot v-else name="fallback">
      <span v-if="compact" class="size-6 shrink-0" />
    </slot>
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
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    logo?: string;
    name?: string;
    compact?: boolean;
    size?: "md" | "lg";
  }>(),
  { size: "md" }
);

const logoClass = computed(() =>
  props.size === "lg"
    ? "size-8 object-cover"
    : "size-6 rounded-2 object-contain"
);
</script>
