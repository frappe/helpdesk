<template>
  <div :class="containerClasses">
    <span :class="spinnerClasses"></span>
    <span v-if="text" class="ml-2">{{ text }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value),
  },
  text: {
    type: String,
    default: '',
  },
  center: {
    type: Boolean,
    default: false,
  },
});

const spinnerClasses = computed(() => {
  const classes = ['loading', 'loading-spinner'];

  // Size mapping
  const sizeMap = {
    xs: 'loading-xs',
    sm: 'loading-sm',
    md: 'loading-md',
    lg: 'loading-lg',
  };

  classes.push(sizeMap[props.size] || 'loading-md');

  return classes.join(' ');
});

const containerClasses = computed(() => {
  const classes = ['flex', 'items-center'];

  if (props.center) {
    classes.push('justify-center', 'w-full', 'h-full', 'min-h-[200px]');
  }

  return classes.join(' ');
});
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
