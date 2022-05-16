<template>
  <div class="flex items-center text-base text-gray-500">
    <LoadingIndicator /> {{ text }}
  </div>
</template>
<script>
import LoadingIndicator from './LoadingIndicator.vue'

export default {
  name: 'Loading',
  props: {
    text: {
      type: String,
      default: 'Loading...',
    },
  },
  components: {
    LoadingIndicator,
  },
}
</script>
