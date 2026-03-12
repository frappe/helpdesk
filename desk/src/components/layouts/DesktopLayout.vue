<template>
  <div class="flex h-screen w-screen">
    <Sidebar />
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <AppHeader />
      <slot />
    </div>
    <Notifications />
    <CommandPalette />
  </div>
</template>
<script setup>
import { Notifications, CommandPalette } from "@/components";
import AppHeader from "./AppHeader.vue";
import Sidebar from "./Sidebar.vue";
</script>
