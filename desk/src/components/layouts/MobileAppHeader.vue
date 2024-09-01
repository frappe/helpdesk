<template>
  <div class="flex border-b h-12 items-center">
    <div class="z-20 -mr-4 ml-1 flex items-center justify-center">
      <Button variant="ghosted" @click="sidebarOpened = !sidebarOpened">
        <FeatherIcon name="menu" class="size-4" />
      </Button>
    </div>
    <header id="app-header" class="w-full"></header>
  </div>
</template>

<script setup>
import { mobileSidebarOpened as sidebarOpened } from "@/composables/mobile";
</script>
