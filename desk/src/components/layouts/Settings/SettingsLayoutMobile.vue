<template>
  <div class="flex h-screen w-screen">
    <SettingsSidebarMobile />
    <div class="flex h-full flex-col flex-1 overflow-auto">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import SettingsSidebarMobile from "./SettingsSidebarMobile.vue";
</script>
