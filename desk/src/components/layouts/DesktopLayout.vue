<template>
  <div class="flex h-screen w-screen">
    <Sidebar />
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <slot />
    </div>
  </div>
</template>
<script setup>
import Sidebar from "./Sidebar.vue";
</script>
