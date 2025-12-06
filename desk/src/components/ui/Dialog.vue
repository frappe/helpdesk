<template>
  <dialog
    ref="dialogRef"
    class="modal"
    :class="{ 'modal-open': modelValue }"
    @click.self="handleBackdropClick"
  >
    <div
      class="modal-box"
      :class="sizeClasses"
    >
      <!-- Header -->
      <div v-if="options.title || $slots.header" class="flex items-center justify-between mb-4">
        <slot name="header">
          <h3 class="font-bold text-lg">{{ options.title }}</h3>
        </slot>
        <button
          v-if="!options.hideCloseButton"
          class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2"
          @click="close"
        >
          ✕
        </button>
      </div>

      <!-- Body -->
      <div class="py-4">
        <slot name="body-content">
          <slot></slot>
        </slot>
      </div>

      <!-- Footer Actions -->
      <div
        v-if="options.actions && options.actions.length > 0"
        class="modal-action"
      >
        <button
          v-for="(action, index) in options.actions"
          :key="index"
          :class="getActionButtonClasses(action)"
          @click="handleAction(action)"
        >
          {{ action.label }}
        </button>
      </div>
    </div>

    <!-- Backdrop -->
    <form method="dialog" class="modal-backdrop" v-if="!options.static">
      <button @click="close">close</button>
    </form>
  </dialog>
</template>

<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  options: {
    type: Object,
    default: () => ({
      title: '',
      size: 'md', // xs, sm, md, lg, xl, full
      hideCloseButton: false,
      static: false, // If true, clicking backdrop won't close
      actions: [], // Array of { label, variant, onClick }
    }),
  },
});

const emit = defineEmits(['update:modelValue', 'close']);

const dialogRef = ref(null);

const sizeClasses = computed(() => {
  const sizeMap = {
    xs: 'max-w-xs',
    sm: 'max-w-sm',
    md: 'max-w-2xl',
    lg: 'max-w-4xl',
    xl: 'max-w-6xl',
    full: 'max-w-full w-full',
  };
  return sizeMap[props.options.size || 'md'] || sizeMap.md;
});

function close() {
  emit('update:modelValue', false);
  emit('close');
}

function handleBackdropClick() {
  if (!props.options.static) {
    close();
  }
}

function getActionButtonClasses(action) {
  const classes = ['btn'];

  const variantMap = {
    solid: 'btn-primary',
    outline: 'btn-outline btn-primary',
    ghost: 'btn-ghost',
    error: 'btn-error',
    success: 'btn-success',
  };

  classes.push(variantMap[action.variant] || 'btn-primary');

  return classes.join(' ');
}

function handleAction(action) {
  if (action.onClick) {
    action.onClick();
  }
}

// Watch for modelValue changes to manage dialog state
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && dialogRef.value) {
      dialogRef.value.showModal?.();
    } else if (dialogRef.value) {
      dialogRef.value.close?.();
    }
  },
  { immediate: true }
);
</script>

<style scoped>
/* Dialog backdrop styling */
.modal-backdrop {
  background-color: rgba(0, 0, 0, 0.3);
}
</style>
