<template>
  <div class="m-auto rounded bg-gray-50 p-2.5 text-base text-gray-700">
    {{ message }}
  </div>
</template>

<script setup lang="ts">
interface P {
  message: string;
}

defineProps<P>();
</script>
