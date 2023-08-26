<template>
  <div class="bg-gray-200">
    <div class="container mx-auto flex h-screen w-screen flex-col">
      <CLayoutNav class="mb-2.5" />
      <RouterView class="grow overflow-hidden rounded-t bg-white" />
    </div>
  </div>
</template>

<script setup lang="ts">
import CLayoutNav from "./CLayoutNav.vue";
</script>
