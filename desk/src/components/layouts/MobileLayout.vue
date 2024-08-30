<template>
  <div class="flex h-screen w-screen">
    <SideBar />
    <div class="flex h-full flex-1 flex-col overflow-auto">
      <slot />
    </div>
  </div>
</template>
<script setup>
import SideBar from "./SideBar.vue";
</script>
