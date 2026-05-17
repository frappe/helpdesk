<template>
  <div
    class="h-3 w-3 rounded-full"
    :class="statusClass"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
  },
})

const statusClass = computed(() => {
  switch (props.status) {
    case 'Backlog':
      return 'bg-gray-400'

    case 'Todo':
      return 'bg-blue-500'

    case 'In Progress':
      return 'bg-yellow-500'

    case 'Done':
      return 'bg-green-500'

    case 'Canceled':
      return 'bg-red-500'

    default:
      return 'bg-gray-400'
  }
})
</script>
