<template>
  <button
    :type="type"
    :class="buttonClasses"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <!-- Prefix icon/slot -->
    <span v-if="loading" class="loading loading-spinner loading-xs"></span>
    <slot v-else-if="$slots.prefix" name="prefix"></slot>
    <component
      v-else-if="icon && iconPosition === 'left'"
      :is="iconComponent"
      :name="icon"
      class="h-4 w-4"
    />

    <!-- Label -->
    <span v-if="label">{{ label }}</span>
    <slot v-else></slot>

    <!-- Suffix icon/slot -->
    <slot v-if="$slots.suffix" name="suffix"></slot>
    <component
      v-else-if="icon && iconPosition === 'right'"
      :is="iconComponent"
      :name="icon"
      class="h-4 w-4"
    />
  </button>
</template>

<script setup>
import { computed } from 'vue';
import { FeatherIcon } from '@/components/ui';

const props = defineProps({
  label: {
    type: String,
    default: '',
  },
  variant: {
    type: String,
    default: 'solid',
    validator: (value) => ['solid', 'outline', 'ghost', 'minimal', 'subtle', 'link'].includes(value),
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value),
  },
  icon: {
    type: String,
    default: null,
  },
  iconPosition: {
    type: String,
    default: 'left',
    validator: (value) => ['left', 'right'].includes(value),
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: 'button',
  },
  theme: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'neutral', 'accent', 'success', 'warning', 'error', 'info'].includes(value),
  },
});

const emit = defineEmits(['click']);

const iconComponent = FeatherIcon;

const buttonClasses = computed(() => {
  const classes = ['btn btn-square'];

  // Size mapping
  const sizeMap = {
    xs: 'btn-xs',
    sm: 'btn-sm',
    md: '',
    lg: 'btn-lg',
  };
  if (sizeMap[props.size]) classes.push(sizeMap[props.size]);

  // Variant + Theme mapping
  if (props.variant === 'solid') {
    const themeMap = {
      primary: 'btn-primary',
      secondary: 'btn-secondary',
      neutral: 'btn-neutral',
      accent: 'btn-accent',
      success: 'btn-success',
      warning: 'btn-warning',
      error: 'btn-error',
      info: 'btn-info',
    };
    classes.push(themeMap[props.theme] || 'btn-primary');
  } else if (props.variant === 'outline') {
    classes.push('btn-outline');
    const themeMap = {
      primary: 'btn-primary',
      secondary: 'btn-secondary',
      neutral: 'btn-neutral',
      accent: 'btn-accent',
      success: 'btn-success',
      warning: 'btn-warning',
      error: 'btn-error',
      info: 'btn-info',
    };
    classes.push(themeMap[props.theme] || 'btn-primary');
  } else if (props.variant === 'ghost') {
    classes.push('btn-ghost');
  } else if (props.variant === 'link') {
    classes.push('btn-link');
  } else if (props.variant === 'minimal' || props.variant === 'subtle') {
    // Minimal/subtle variant - no background, just hover
    classes.push('btn-ghost');
  }

  // Gap between icon and text
  if ((props.icon || props.$slots.prefix || props.$slots.suffix) && (props.label || props.$slots.default)) {
    classes.push('gap-2');
  }

  return classes.join(' ');
});

function handleClick(event) {
  if (!props.disabled && !props.loading) {
    emit('click', event);
  }
}
</script>

<style scoped>
/* Additional custom styles if needed */
</style>
