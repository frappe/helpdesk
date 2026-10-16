<template>
  <div
    class="grid transition-[grid-template-rows] duration-200 ease-out motion-reduce:transition-none"
    :class="open ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
    :inert="!open"
  >
    <div class="min-h-0 overflow-hidden">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
// Rows 0fr -> 1fr animate to the content's own height; inert keeps it out of the tab order.
defineProps<{ open: boolean }>();
</script>
