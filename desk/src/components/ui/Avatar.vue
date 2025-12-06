<template>
  <div :class="avatarClasses">
    <div v-if="image" class="w-full h-full">
      <img :src="image" :alt="label || 'Avatar'" />
    </div>
    <div v-else-if="label" class="placeholder">
      <div :class="placeholderClasses">
        <span>{{ initials }}</span>
      </div>
    </div>
    <div v-else class="placeholder">
      <div :class="placeholderClasses">
        <FeatherIcon name="user" class="h-1/2 w-1/2" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { FeatherIcon } from '@/components/ui';

const props = defineProps({
  image: {
    type: String,
    default: null,
  },
  label: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(value),
  },
  shape: {
    type: String,
    default: 'circle',
    validator: (value) => ['circle', 'square'].includes(value),
  },
});

const initials = computed(() => {
  if (!props.label) return '';

  const names = props.label.trim().split(' ');
  if (names.length === 1) {
    return names[0].substring(0, 2).toUpperCase();
  }

  return (names[0][0] + names[names.length - 1][0]).toUpperCase();
});

const avatarClasses = computed(() => {
  const classes = ['avatar'];

  // Shape
  if (props.shape === 'square') {
    classes.push('avatar-square');
  }

  // Size
  const sizeMap = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };
  classes.push(sizeMap[props.size] || sizeMap.md);

  return classes.join(' ');
});

const placeholderClasses = computed(() => {
  const classes = ['bg-neutral', 'text-neutral-content'];

  // Make placeholder rounded based on shape
  if (props.shape === 'circle') {
    classes.push('rounded-full');
  } else {
    classes.push('rounded');
  }

  // Full size to fill avatar container
  classes.push('w-full', 'h-full', 'flex', 'items-center', 'justify-center');

  return classes.join(' ');
});
</script>

<style scoped>
.avatar img {
  object-fit: cover;
}
</style>
