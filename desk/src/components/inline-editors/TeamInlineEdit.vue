<template>
  <div v-if="editable" @click.stop>
    <Dropdown :options="teamOptions">
      <template #default="{ open }">
        <Button
          :label="displayTeam"
          @click="open"
          class="w-full justify-start"
        />
      </template>
    </Dropdown>
  </div>
  <div v-else>
    <span>{{ displayTeam }}</span>
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

// Fetch available teams
const teamsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'HD Team',
    fields: ['name'],
    filters: {},
    order_by: 'name asc',
  },
  auto: true,
});

const teamOptions = computed(() => {
  if (!teamsResource.data) return [];
  return teamsResource.data.map(team => ({
    label: team.name,
    onClick: () => handleSelect(team.name),
  }));
});

const displayTeam = computed(() => {
  return props.modelValue || 'No Team';
});

function handleSelect(newValue) {
  // Immediately save when dropdown selection is made
  console.log('[TeamInlineEdit] handleSelect called:', newValue);
  emit('update:modelValue', newValue);
  emit('updated', { field: 'agent_group', value: newValue });
  console.log('[TeamInlineEdit] Events emitted');
}
</script>

<style scoped>
/* Team-specific styles if needed */
</style>
