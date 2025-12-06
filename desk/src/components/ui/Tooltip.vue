<template>
  <div
    class="tooltip"
    :class="tooltipClasses"
    :data-tip="text"
  >
    <slot></slot>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  text: {
    type: String,
    required: true,
  },
  placement: {
    type: String,
    default: 'top',
    validator: (value) => ['top', 'bottom', 'left', 'right'].includes(value),
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'primary', 'secondary', 'accent', 'info', 'success', 'warning', 'error'].includes(value),
  },
});

const tooltipClasses = computed(() => {
  const classes = [];

  // Placement
  const placementMap = {
    top: 'tooltip-top',
    bottom: 'tooltip-bottom',
    left: 'tooltip-left',
    right: 'tooltip-right',
  };
  classes.push(placementMap[props.placement] || 'tooltip-top');

  // Variant/Color
  const variantMap = {
    default: '',
    primary: 'tooltip-primary',
    secondary: 'tooltip-secondary',
    accent: 'tooltip-accent',
    info: 'tooltip-info',
    success: 'tooltip-success',
    warning: 'tooltip-warning',
    error: 'tooltip-error',
  };
  if (variantMap[props.variant]) {
    classes.push(variantMap[props.variant]);
  }

  return classes.join(' ');
});
</script>

<style scoped>
/* Tooltip inherits from DaisyUI, no additional styles needed */
</style>
