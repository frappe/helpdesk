<template>
  <div class="text-sm breadcrumbs">
    <ul>
      <li v-for="(item, index) in items" :key="index">
        <a
          v-if="item.route || item.onClick"
          :href="item.route"
          :class="{ 'font-semibold': index === items.length - 1 }"
          @click.prevent="handleClick(item)"
        >
          <component
            v-if="item.icon"
            :is="iconComponent"
            :name="item.icon"
            class="h-4 w-4 mr-1"
          />
          {{ item.label }}
        </a>
        <span v-else :class="{ 'font-semibold': index === items.length - 1 }">
          <component
            v-if="item.icon"
            :is="iconComponent"
            :name="item.icon"
            class="h-4 w-4 mr-1"
          />
          {{ item.label }}
        </span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { FeatherIcon } from '@/components/ui';

const props = defineProps({
  items: {
    type: Array,
    required: true,
    // Items format: { label, route?, icon?, onClick? }
  },
});

const emit = defineEmits(['click']);

const iconComponent = FeatherIcon;

function handleClick(item) {
  if (item.onClick) {
    item.onClick();
  }
  emit('click', item);
}
</script>
