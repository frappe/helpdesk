<template>
  <div class="m-auto rounded bg-gray-100 p-2.5">
    <div class="text-base font-medium text-gray-700">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
interface P {
  message: string;
}

defineProps<P>();
</script>
