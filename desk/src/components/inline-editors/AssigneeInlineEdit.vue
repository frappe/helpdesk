<template>
  <InlineEditCell
    :model-value="currentAssignee"
    :display-value="displayAssignee"
    :editable="editable"
    @save="handleSave"
  >
    <template #display="{ value }">
      <span>{{ displayAssignee }}</span>
    </template>
    <template #editor="{ update }">
      <Autocomplete
        :value="currentAssignee"
        :options="agentOptions"
        @change="(option) => update(option?.name || null)"
        placeholder="Search agents..."
      />
    </template>
  </InlineEditCell>
</template>

<script setup>
import { computed } from 'vue';
import { createResource } from '@/components/ui';
import InlineEditCell from '../InlineEditCell.vue';
import { Autocomplete } from 'frappe-ui';

const props = defineProps({
  modelValue: {
    type: [String, Array],
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

// Parse the _assign field which comes as a JSON string array like '["user@example.com"]'
const currentAssignee = computed(() => {
  if (!props.modelValue) return null;

  // If it's already a string (single user), return it
  if (typeof props.modelValue === 'string' && !props.modelValue.startsWith('[')) {
    return props.modelValue;
  }

  // If it's a JSON array string, parse and get first assignee
  try {
    const parsed = typeof props.modelValue === 'string'
      ? JSON.parse(props.modelValue)
      : props.modelValue;

    return Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : null;
  } catch (e) {
    console.error('[AssigneeInlineEdit] Error parsing assignee:', e);
    return null;
  }
});

// Fetch available agents
const agentsResource = createResource({
  url: 'helpdesk.helpdesk.doctype.hd_ticket.api.get_agents',
  auto: true,
});

const agentOptions = computed(() => {
  if (!agentsResource.data) return [];
  return agentsResource.data.map(agent => ({
    label: agent.agent_name || agent.name,
    name: agent.name,
    value: agent.name,
  }));
});

const displayAssignee = computed(() => {
  if (!currentAssignee.value) return 'Unassigned';

  const agent = agentOptions.value.find(a => a.name === currentAssignee.value);
  return agent?.label || currentAssignee.value;
});

function handleSave(newValue) {
  console.log('[AssigneeInlineEdit] Saving new assignee:', newValue);

  // For Frappe's _assign field, we need to use the add/remove assignment API
  // instead of directly setting the field value
  emit('update:modelValue', newValue);
  emit('updated', {
    field: '_assign',
    value: newValue,
    action: 'assign' // Special flag to indicate this needs assignment API
  });
}
</script>

<style scoped>
/* Assignee-specific styles if needed */
</style>
