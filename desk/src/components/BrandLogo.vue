<template>
  <img
    v-if="config.brandLogo"
    :src="config.brandLogo"
    alt="Brand Logo"
    class="h-8 w-8 shrink-0 object-cover"
  />
  <HDLogo v-else class="h-8 w-8 shrink-0 rounded" />
</template>

<script setup lang="ts">
import HDLogo from "@/assets/logos/HDLogo.vue";

import { useConfigStore } from "@/stores/config";
const config = useConfigStore();
</script>

<style scoped></style>
