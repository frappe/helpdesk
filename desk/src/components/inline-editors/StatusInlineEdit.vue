<template>
  <div v-if="editable" @click.stop>
    <Dropdown :options="statusOptions">
      <template #default="{ open }">
        <Button
          :label="displayStatus"
          @click="open"
          class="w-full justify-start"
        >
          <template #prefix>
            <IndicatorIcon :class="statusColor" />
          </template>
        </Button>
      </template>
    </Dropdown>
  </div>
  <div v-else class="flex items-center">
    <IndicatorIcon :class="statusColor" />
    <span class="ml-2">{{ displayStatus }}</span>
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

// Fetch available statuses
const statusesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'HD Ticket Status',
    fields: ['name'],
    filters: {},
    order_by: 'name asc',
  },
  auto: true,
});

const statusOptions = computed(() => {
  if (!statusesResource.data) return [];
  return statusesResource.data.map(status => ({
    label: status.name,
    onClick: () => handleSelect(status.name),
  }));
});

const displayStatus = computed(() => {
  return props.modelValue || 'No Status';
});

const statusColor = computed(() => {
  // Default gray color since we can't fetch color field
  return 'text-gray-500';
});

function handleSelect(newValue) {
  // Immediately save when dropdown selection is made
  console.log('[StatusInlineEdit] handleSelect called:', newValue);
  emit('update:modelValue', newValue);
  emit('updated', { field: 'status', value: newValue });
  console.log('[StatusInlineEdit] Events emitted');
}
</script>

<style scoped>
/* Status-specific styles if needed */
</style>
