<template>
  <Tooltip :text="__('View documentation')">
    <a :href="url" target="_blank">
      <lucide-circle-question-mark
        class="h-4 w-4 text-ink-gray-6"
        :class="color"
      />
    </a>
  </Tooltip>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
defineProps<{
  url: string;
  color?: string;
}>();
</script>

<style scoped></style>
