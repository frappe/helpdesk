<template>
  <div :class="containerClasses">
    <!-- Label -->
    <label v-if="label" class="label">
      <span class="label-text">
        {{ label }}
        <span v-if="required" class="text-error ml-1">*</span>
      </span>
    </label>

    <!-- Input based on type -->
    <textarea
      v-if="type === 'textarea'"
      v-model="internalValue"
      :class="inputClasses"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      @input="handleInput"
      @blur="handleBlur"
    ></textarea>

    <select
      v-else-if="type === 'select'"
      v-model="internalValue"
      :class="selectClasses"
      :disabled="disabled"
      @change="handleInput"
      @blur="handleBlur"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

    <input
      v-else
      v-model="internalValue"
      :type="type"
      :class="inputClasses"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="handleInput"
      @blur="handleBlur"
    />

    <!-- Error/Help Text -->
    <label v-if="errorMessage || helpText" class="label">
      <span v-if="errorMessage" class="label-text-alt text-error">
        {{ errorMessage }}
      </span>
      <span v-else-if="helpText" class="label-text-alt">
        {{ helpText }}
      </span>
    </label>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  label: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: 'text',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['xs', 'sm', 'md', 'lg'].includes(value),
  },
  variant: {
    type: String,
    default: 'bordered',
    validator: (value) => ['bordered', 'ghost', 'subtle'].includes(value),
  },
  placeholder: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  required: {
    type: Boolean,
    default: false,
  },
  errorMessage: {
    type: String,
    default: '',
  },
  helpText: {
    type: String,
    default: '',
  },
  rows: {
    type: Number,
    default: 3,
  },
  options: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['update:modelValue', 'change', 'blur']);

const internalValue = ref(props.modelValue);

watch(
  () => props.modelValue,
  (newVal) => {
    internalValue.value = newVal;
  }
);

const containerClasses = computed(() => {
  const classes = ['form-control', 'w-full'];
  return classes.join(' ');
});

const baseInputClasses = computed(() => {
  const classes = [];

  // Size
  const sizeMap = {
    xs: 'input-xs',
    sm: 'input-sm',
    md: 'input-md',
    lg: 'input-lg',
  };
  classes.push(sizeMap[props.size] || 'input-md');

  // Variant
  if (props.variant === 'bordered') {
    classes.push('input-bordered');
  } else if (props.variant === 'ghost') {
    classes.push('input-ghost');
  }

  // Error state
  if (props.errorMessage) {
    classes.push('input-error');
  }

  // Full width
  classes.push('w-full');

  return classes;
});

const inputClasses = computed(() => {
  const classes = ['input', ...baseInputClasses.value];
  return classes.join(' ');
});

const selectClasses = computed(() => {
  const classes = ['select', ...baseInputClasses.value];
  return classes.join(' ');
});

function handleInput(event) {
  const value = event.target.value;
  internalValue.value = value;
  emit('update:modelValue', value);
  emit('change', value);
}

function handleBlur(event) {
  emit('blur', event);
}
</script>

<style scoped>
/* FormControl inherits from DaisyUI form styles */
</style>
