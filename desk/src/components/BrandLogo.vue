<template>
  <Avatar v-if="config.brandLogo" size="xl" :image="config.brandLogo" />
  <HDLogo v-else class="h-8 w-8 shrink-0 rounded" />
</template>

<script setup lang="ts">
import { Avatar } from "frappe-ui";
import HDLogo from "@/assets/logos/HDLogo.vue";

import { useConfigStore } from "@/stores/config";
const config = useConfigStore();
</script>

<style scoped></style>
