<template>
  <div v-if="editable" @click.stop>
    <Dropdown :options="typeOptions">
      <template #default="{ open }">
        <Button
          :label="displayType"
          @click="open"
          class="w-full justify-start"
        />
      </template>
    </Dropdown>
  </div>
  <div v-else>
    <span>{{ displayType }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Button, Dropdown, createResource } from '@/components/ui';

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

// Fetch available ticket types
const ticketTypesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'HD Ticket Type',
    fields: ['name'],
    filters: {},
    order_by: 'name asc',
  },
  auto: true,
});

const typeOptions = computed(() => {
  if (!ticketTypesResource.data) return [];
  return ticketTypesResource.data.map(type => ({
    label: type.name,
    onClick: () => handleSelect(type.name),
  }));
});

const displayType = computed(() => {
  return props.modelValue || 'No Type';
});

function handleSelect(newValue) {
  console.log('[TicketTypeInlineEdit] handleSelect called:', newValue);
  emit('update:modelValue', newValue);
  emit('updated', { field: 'ticket_type', value: newValue });
}
</script>

<style scoped>
/* Ticket Type-specific styles if needed */
</style>
