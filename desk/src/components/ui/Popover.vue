<template>
  <div class="dropdown" :class="dropdownClasses">
    <!-- Trigger -->
    <label tabindex="0">
      <slot name="trigger">
        <slot></slot>
      </slot>
    </label>

    <!-- Popover Content -->
    <div
      tabindex="0"
      class="dropdown-content card compact bg-base-100 shadow-lg rounded-box"
      :class="contentClasses"
    >
      <div class="card-body">
        <slot name="content">
          <slot name="body"></slot>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  placement: {
    type: String,
    default: 'bottom',
    validator: (value) => ['top', 'bottom', 'left', 'right', 'bottom-start', 'bottom-end', 'top-start', 'top-end'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value),
  },
  hover: {
    type: Boolean,
    default: false,
  },
});

const dropdownClasses = computed(() => {
  const classes = [];

  // Placement
  const placementMap = {
    top: 'dropdown-top',
    bottom: 'dropdown-bottom',
    left: 'dropdown-left',
    right: 'dropdown-right',
    'bottom-start': 'dropdown-bottom dropdown-start',
    'bottom-end': 'dropdown-bottom dropdown-end',
    'top-start': 'dropdown-top dropdown-start',
    'top-end': 'dropdown-top dropdown-end',
  };
  classes.push(placementMap[props.placement] || 'dropdown-bottom');

  // Hover trigger
  if (props.hover) {
    classes.push('dropdown-hover');
  }

  return classes.join(' ');
});

const contentClasses = computed(() => {
  const classes = ['border', 'border-base-300'];

  // Size
  const sizeMap = {
    sm: 'w-48',
    md: 'w-64',
    lg: 'w-80',
    xl: 'w-96',
  };
  classes.push(sizeMap[props.size] || 'w-64');

  return classes.join(' ');
});
</script>

<style scoped>
.dropdown-content {
  z-index: 50;
}
</style>
