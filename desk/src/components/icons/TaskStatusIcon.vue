<!-- TaskStatusIcon.vue — drop-in replacement if yours doesn't match the screenshot -->
<template>
  <span class="flex items-center justify-center" style="width:16px;height:16px">
    <!-- Backlog: dashed circle -->
    <svg v-if="status === 'Backlog'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="6.5" stroke="#888" stroke-width="1.5" stroke-dasharray="3 2" />
    </svg>
    <!-- Todo: plain circle outline -->
    <svg v-else-if="status === 'Todo'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="6.5" stroke="#555" stroke-width="1.5" />
    </svg>

    <!-- In Progress: half-filled circle -->
    <svg v-else-if="status === 'In Progress'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="6.5" stroke="#555" stroke-width="1.5" />
      <path d="M8 1.5 A6.5 6.5 0 0 1 8 14.5 Z" fill="#555" />
    </svg>
    <!-- Done: filled circle with checkmark -->
    <svg v-else-if="status === 'Done'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#1a1a1a" />
      <path d="M5 8.5l2 2 4-4" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <!-- Canceled: filled circle with X -->
    <svg v-else-if="status === 'Canceled'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="7" fill="#1a1a1a" />
      <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke="white" stroke-width="1.5" stroke-linecap="round" />
    </svg>
    <!-- Fallback -->
    <svg v-else viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <circle cx="8" cy="8" r="6.5" stroke="#888" stroke-width="1.5" stroke-dasharray="3 2" />
    </svg>
  </span>
</template>




<script setup lang="ts">
defineProps<{ status: string }>()
</script>