<template>
  <InlineEditCell
    :model-value="modelValue"
    :display-value="modelValue || 'No Subject'"
    :editable="editable"
    @save="handleSave"
  >
    <template #display="{ value }">
      <span class="truncate">{{ value }}</span>
    </template>
    <template #editor="{ update }">
      <input
        type="text"
        :value="modelValue"
        @input="(e) => update(e.target.value)"
        @keydown.enter="(e) => { e.preventDefault(); e.target.blur(); }"
        class="w-full px-2 py-1 border border-gray-300 rounded focus:outline-none focus:border-blue-500"
        placeholder="Enter subject..."
        autofocus
      />
    </template>
  </InlineEditCell>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue';
import InlineEditCell from '../InlineEditCell.vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
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

function handleSave(newValue) {
  if (newValue && newValue.trim() !== '') {
    emit('update:modelValue', newValue);
    emit('updated', { field: 'subject', value: newValue });
  }
}
</script>

<style scoped>
/* Subject-specific styles if needed */
</style>
