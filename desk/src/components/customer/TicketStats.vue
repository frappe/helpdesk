<template>
  <div class="p-5"></div>
</template>

<script setup lang="ts">
const props = defineProps<{
  dt: "HD Customer" | "Contact";
  dn: string;
}>();
</script>
