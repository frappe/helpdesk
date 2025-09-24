<template>
  <div class="flex h-screen w-screen">
    <SettingsSidebarDesktop />
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import SettingsSidebarDesktop from "./SettingsSidebarDesktop.vue";
</script>
