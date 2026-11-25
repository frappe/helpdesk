<template>
  <img
    v-if="isImageIcon(icon)"
    :src="icon"
    alt=""
    class="shrink-0 object-contain"
  />
  <span
    v-else
    :class="categoryIcon(icon)"
    class="shrink-0"
    aria-hidden="true"
  />
</template>

<script setup lang="ts">
import { categoryIcon, isImageIcon } from "./categoryIcons";

defineProps<{ icon?: string | null }>();
</script>
