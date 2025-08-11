<template>
  <Tooltip text="View documentation">
    <a :href="url" target="_blank">
      <lucide-info class="h-4 w-4 text-ink-gray-6" :class="color" />
    </a>
  </Tooltip>
</template>

<script setup lang="ts">
defineProps<{
  url: string;
  color?: string;
}>();
</script>

<style scoped></style>
