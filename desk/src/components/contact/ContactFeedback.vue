<template>
  <div>{{ name }}</div>
</template>

<script setup lang="ts">
// props name as type string
const props = defineProps<{
  name: string;
}>();
</script>

<style scoped></style>
