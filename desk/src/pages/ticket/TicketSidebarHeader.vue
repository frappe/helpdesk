<template>
  <div class="border-b px-5 py-1.5">
    <span class="text-base font-medium">
      {{ title }}
    </span>
  </div>
</template>

<script setup lang="ts">
interface P {
  title: string;
}

defineProps<P>();
</script>
