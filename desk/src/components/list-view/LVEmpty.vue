<template>
  <div
    class="flex h-full w-full items-center justify-center text-base text-gray-700"
  >
    <EmptyMessage :message="message" />
  </div>
</template>

<script setup lang="ts">
import EmptyMessage from "../EmptyMessage.vue";

interface P {
  message: string;
}

defineProps<P>();
</script>
