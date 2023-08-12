<template>
  <div class="m-auto w-max text-base text-gray-700">
    {{ message }}
  </div>
</template>

<script setup lang="ts">
defineProps<{ message: string }>();
</script>
