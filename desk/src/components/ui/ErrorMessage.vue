<template>
  <div v-if="message" :class="alertClasses" role="alert">
    <component
      v-if="icon"
      :is="iconComponent"
      :name="icon"
      class="h-5 w-5 shrink-0"
    />
    <component
      v-else
      :is="iconComponent"
      name="alert-circle"
      class="h-5 w-5 shrink-0"
    />
    <span>{{ message }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { FeatherIcon } from '@/components/ui';

const props = defineProps({
  message: {
    type: String,
    required: true,
  },
  variant: {
    type: String,
    default: 'error',
    validator: (value) => ['error', 'warning', 'info', 'success'].includes(value),
  },
  icon: {
    type: String,
    default: '',
  },
});

const iconComponent = FeatherIcon;

const alertClasses = computed(() => {
  const classes = ['alert', 'flex', 'items-center', 'gap-2'];

  // Variant
  const variantMap = {
    error: 'alert-error',
    warning: 'alert-warning',
    info: 'alert-info',
    success: 'alert-success',
  };
  classes.push(variantMap[props.variant] || 'alert-error');

  return classes.join(' ');
});
</script>
