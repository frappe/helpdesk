<template>
  <Badge
    theme="gray"
    variant="outline"
    size="lg"
    class="max-w-40 gap-1.5 transition-colors duration-150 hover:bg-surface-gray-2"
  >
    <span
      class="size-2 shrink-0 rounded-full"
      :style="{ backgroundColor: color }"
    />
    <span :title="tag" class="min-w-0 truncate text-ink-gray-7">{{ tag }}</span>
  </Badge>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";

defineProps<{ tag: string; color: string }>();
</script>
