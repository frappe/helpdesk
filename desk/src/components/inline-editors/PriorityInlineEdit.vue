<template>
  <div v-if="editable" @click.stop>
    <Dropdown :options="priorityOptions">
      <template #default="{ open }">
        <Button
          :label="displayPriority"
          @click="open"
          class="w-full justify-start"
        >
          <template #prefix>
            <IndicatorIcon :class="priorityColor" />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
  <div v-else class="flex items-center">
    <IndicatorIcon :class="priorityColor" />
    <span class="ml-2">{{ displayPriority }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Button, Dropdown, createResource } from '@/components/ui';
import { IndicatorIcon } from '../icons';

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  ticketId: {
    type: String,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:modelValue', 'updated']);

// Fetch available priorities
const prioritiesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'HD Ticket Priority',
    fields: ['name'],
    filters: {},
    order_by: 'name asc',
  },
  auto: true,
});

const priorityOptions = computed(() => {
  if (!prioritiesResource.data) return [];
  return prioritiesResource.data.map(priority => ({
    label: priority.name,
    onClick: () => handleSelect(priority.name),
  }));
});

const displayPriority = computed(() => {
  return props.modelValue || 'No Priority';
});

const priorityColor = computed(() => {
  // Default gray color since we can't fetch color field
  return 'text-gray-500';
});

function handleSelect(newValue) {
  // Immediately save when dropdown selection is made
  console.log('[PriorityInlineEdit] handleSelect called:', newValue);
  emit('update:modelValue', newValue);
  emit('updated', { field: 'priority', value: newValue });
  console.log('[PriorityInlineEdit] Events emitted');
}
</script>

<style scoped>
/* Priority-specific styles if needed */
</style>
