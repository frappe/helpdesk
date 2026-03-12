<template>
  <div class="flex h-screen w-screen">
    <MobileSidebar />
    <div class="flex h-full flex-col flex-1 overflow-auto bg-surface-white">
      <MobileAppHeader />
      <slot />
    </div>
  </div>
</template>
<script setup>
import MobileSidebar from "./MobileSidebar.vue";
import MobileAppHeader from "./MobileAppHeader.vue";
</script>
