<template>
  <div class="w-[106px] shrink-0 truncate text-sm text-ink-gray-5">
    <Tooltip :text="__(label)">
      <span>{{ __(label) }}</span>
    </Tooltip>
    <span v-if="required" class="text-ink-red-6"> * </span>
  </div>
</template>

<script setup lang="ts">
import { Tooltip } from "frappe-ui";

defineProps<{
  label: string;
  required?: boolean;
}>();
</script>
