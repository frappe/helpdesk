<template>
  <div class="flex flex-col gap-1">
    <SidebarLink
      v-for="option in options"
      v-bind="option"
      :key="option.label"
    />
  </div>
</template>

<script setup lang="ts">
import SidebarLink from "./SidebarLink.vue";

defineProps({
  options: {
    type: Array,
    required: true,
  },
});
</script>
