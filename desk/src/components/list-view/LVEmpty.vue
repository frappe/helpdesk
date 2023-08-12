<template>
  <div
    class="flex h-full w-full items-center justify-center text-base text-gray-700"
  >
    <EmptyMessage :message="emptyMessage" />
  </div>
</template>

<script setup lang="ts">
import EmptyMessage from "../EmptyMessage.vue";

defineProps<{ emptyMessage: string }>();
</script>
