<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-gray-50">
      <SideBar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <slot />
    </div>
  </div>
</template>
<script setup>
import SideBar from "./SideBar.vue";
</script>
