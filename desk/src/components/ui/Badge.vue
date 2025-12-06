<template>
  <span :class="badgeClasses">
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  variant: {
    type: String,
    default: 'neutral',
    validator: (value) => [
      'neutral',
      'primary',
      'secondary',
      'accent',
      'ghost',
      'info',
      'success',
      'warning',
      'error',
    ].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value),
  },
  outline: {
    type: Boolean,
    default: false,
  },
});

const badgeClasses = computed(() => {
  const classes = ['badge'];

  // Variant/Color
  const variantMap = {
    neutral: 'badge-neutral',
    primary: 'badge-primary',
    secondary: 'badge-secondary',
    accent: 'badge-accent',
    ghost: 'badge-ghost',
    info: 'badge-info',
    success: 'badge-success',
    warning: 'badge-warning',
    error: 'badge-error',
  };
  classes.push(variantMap[props.variant] || 'badge-neutral');

  // Size
  const sizeMap = {
    xs: 'badge-xs',
    sm: 'badge-sm',
    md: '',
    lg: 'badge-lg',
  };
  if (sizeMap[props.size]) classes.push(sizeMap[props.size]);

  // Outline
  if (props.outline) {
    classes.push('badge-outline');
  }

  return classes.join(' ');
});
</script>

<style scoped>
/* Additional badge styling if needed */
</style>
