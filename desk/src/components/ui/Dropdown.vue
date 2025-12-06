<template>
  <div class="dropdown" :class="dropdownClasses">
    <!-- Trigger -->
    <label tabindex="0" class="cursor-pointer">
      <slot>
        <button class="btn">
          {{ label || 'Menu' }}
          <FeatherIcon name="chevron-down" class="h-4 w-4 ml-1" />
        </button>
      </slot>
    </label>

    <!-- Menu -->
    <ul
      tabindex="0"
      class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-[1]"
      :class="menuClasses"
    >
      <template v-for="(option, index) in options" :key="index">
        <!-- Divider -->
        <li v-if="option.divider" class="divider my-1"></li>

        <!-- Group header -->
        <li v-else-if="option.group" class="menu-title">
          <span>{{ option.group }}</span>
        </li>

        <!-- Menu item -->
        <li v-else>
          <a
            @click="handleOptionClick(option)"
            :class="{ 'active': option.active, 'disabled': option.disabled }"
          >
            <component
              v-if="option.icon"
              :is="iconComponent"
              :name="option.icon"
              class="h-4 w-4"
            />
            <component v-else-if="option.iconComponent" :is="option.iconComponent" />
            <span>{{ option.label }}</span>
            <span v-if="option.shortcut" class="text-xs opacity-50">{{ option.shortcut }}</span>
          </a>
        </li>
      </template>
    </ul>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { FeatherIcon } from '@/components/ui';

const props = defineProps({
  options: {
    type: Array,
    required: true,
    // Options format: { label, value, icon, onClick, divider, group, active, disabled }
  },
  label: {
    type: String,
    default: '',
  },
  placement: {
    type: String,
    default: 'bottom',
    validator: (value) => ['top', 'bottom', 'left', 'right', 'bottom-end', 'bottom-start', 'top-end', 'top-start'].includes(value),
  },
});

const emit = defineEmits(['select']);

const iconComponent = FeatherIcon;

const dropdownClasses = computed(() => {
  const classes = [];

  // Placement
  const placementMap = {
    top: 'dropdown-top',
    bottom: 'dropdown-bottom',
    left: 'dropdown-left',
    right: 'dropdown-right',
    'bottom-end': 'dropdown-end',
    'bottom-start': 'dropdown-start',
    'top-end': 'dropdown-top dropdown-end',
    'top-start': 'dropdown-top dropdown-start',
  };
  classes.push(placementMap[props.placement] || 'dropdown-bottom');

  return classes.join(' ');
});

const menuClasses = computed(() => {
  const classes = [];

  // Add shadow and border
  classes.push('border', 'border-base-300');

  return classes.join(' ');
});

function handleOptionClick(option) {
  if (option.disabled) return;

  if (option.onClick) {
    option.onClick();
  }

  emit('select', option);

  // Close dropdown after selection
  if (document.activeElement) {
    document.activeElement.blur();
  }
}
</script>

<style scoped>
/* Ensure dropdown content appears above other elements */
.dropdown-content {
  max-height: 400px;
  overflow-y: auto;
}
</style>
