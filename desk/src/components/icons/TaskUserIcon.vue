<template>
  <div class="inline-flex items-center justify-center shrink-0">
    <img 
      v-if="image" 
      :src="image" 
      :alt="label" 
      class="rounded-full object-cover"
      :class="sizeClasses"
    />
    <div 
      v-else 
      class="rounded-full bg-gray-200 text-gray-700 font-semibold flex items-center justify-center uppercase select-none"
      :class="sizeClasses"
    >
      {{ initials }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps({
  image: { type: String, default: "" },
  label: { type: String, default: "" },
  size:  { type: String, default: "sm" } // 'sm', 'md', 'lg'
});

const sizeClasses = computed(() => {
  if (props.size === 'xs') return 'h-4 w-4 text-[10px]';
  if (props.size === 'md') return 'h-6 w-6 text-xs';
  if (props.size === 'lg') return 'h-8 w-8 text-sm';
  return 'h-5 w-5 text-[11px]'; // default 'sm'
});

const initials = computed(() => {
  if (!props.label?.trim()) return "?";
  return props.label.trim().split(/\s+/).map(w => w[0]).join("").substring(0, 2);
});
</script>