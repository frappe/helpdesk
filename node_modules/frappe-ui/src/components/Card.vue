<template>
  <div class="flex flex-col px-6 py-5 bg-white border rounded-lg shadow">
    <div class="flex items-baseline justify-between">
      <div class="flex items-baseline space-x-2">
        <div class="flex items-center space-x-2" v-if="$slots['actions-left']">
          <slot name="actions-left"></slot>
        </div>
        <h2 class="text-xl font-semibold">{{ title }}</h2>
      </div>
      <div class="flex items-center space-x-2" v-if="$slots['actions']">
        <slot name="actions"></slot>
      </div>
    </div>
    <p class="text-base text-gray-600 mt-1.5" v-if="subtitle">
      {{ subtitle }}
    </p>
    <div
      v-if="loading"
      class="flex flex-col items-center justify-center flex-auto mt-4 rounded-md"
    >
      <LoadingText />
    </div>
    <div class="flex-auto mt-4 overflow-auto" v-else-if="$slots['default']">
      <slot></slot>
    </div>
  </div>
</template>
<script>
import LoadingText from './LoadingText.vue'
export default {
  name: 'Card',
  props: ['title', 'subtitle', 'loading'],
  components: {
    LoadingText,
  },
}
</script>
