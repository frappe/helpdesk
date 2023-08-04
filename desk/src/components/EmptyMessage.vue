<template>
  <div class="m-auto rounded p-2.5">
    <div class="text-base text-gray-700">
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
