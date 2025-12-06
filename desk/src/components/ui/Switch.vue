<template>
  <div :class="containerClasses">
    <input
      type="checkbox"
      :class="switchClasses"
      :checked="modelValue"
      :disabled="disabled"
      @change="handleChange"
    />
    <label v-if="label" class="label cursor-pointer">
      <span class="label-text">{{ label }}</span>
    </label>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  label: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value),
  },
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'accent', 'success', 'warning', 'error', 'info'].includes(value),
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['update:modelValue', 'change']);

const containerClasses = computed(() => {
  const classes = ['form-control'];
  if (props.label) {
    classes.push('flex', 'items-center', 'gap-2');
  }
  return classes.join(' ');
});

const switchClasses = computed(() => {
  const classes = ['toggle'];

  // Size
  const sizeMap = {
    xs: 'toggle-xs',
    sm: 'toggle-sm',
    md: 'toggle-md',
    lg: 'toggle-lg',
  };
  classes.push(sizeMap[props.size] || 'toggle-md');

  // Variant
  const variantMap = {
    primary: 'toggle-primary',
    secondary: 'toggle-secondary',
    accent: 'toggle-accent',
    success: 'toggle-success',
    warning: 'toggle-warning',
    error: 'toggle-error',
    info: 'toggle-info',
  };
  classes.push(variantMap[props.variant] || 'toggle-primary');

  return classes.join(' ');
});

function handleChange(event) {
  const value = event.target.checked;
  emit('update:modelValue', value);
  emit('change', value);
}
</script>
