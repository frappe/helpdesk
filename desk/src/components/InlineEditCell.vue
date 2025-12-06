<template>
  <div class="inline-edit-cell" @click.stop="startEdit" :class="{ 'is-editing': isEditing }">
    <slot v-if="!isEditing" name="display" :value="modelValue">
      {{ displayValue }}
    </slot>
    <div v-else class="inline-edit-wrapper" @click.stop>
      <slot name="editor" :value="modelValue" :update="updateValue">
        <input
          ref="inputRef"
          v-model="editValue"
          class="inline-edit-input"
          @blur="saveEdit"
          @keydown.enter="saveEdit"
          @keydown.esc="cancelEdit"
        />
      </slot>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';

const props = defineProps({
  modelValue: {
    type: [String, Number, Boolean, null],
    default: null
  },
  displayValue: {
    type: String,
    default: ''
  },
  editable: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['update:modelValue', 'save']);

const isEditing = ref(false);
const editValue = ref(props.modelValue);
const inputRef = ref(null);

watch(() => props.modelValue, (newVal) => {
  editValue.value = newVal;
});

async function startEdit() {
  if (!props.editable) return;

  isEditing.value = true;
  editValue.value = props.modelValue;

  await nextTick();
  inputRef.value?.focus();
}

function updateValue(value) {
  editValue.value = value;
}

function saveEdit() {
  if (editValue.value !== props.modelValue) {
    emit('update:modelValue', editValue.value);
    emit('save', editValue.value);
  }
  isEditing.value = false;
}

function cancelEdit() {
  editValue.value = props.modelValue;
  isEditing.value = false;
}
</script>

<style scoped>
.inline-edit-cell {
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  min-height: 2rem;
  display: flex;
  align-items: center;
}

.inline-edit-cell:hover:not(.is-editing) {
  background-color: var(--gray-50);
}

.inline-edit-cell.is-editing {
  padding: 0;
}

.inline-edit-wrapper {
  width: 100%;
}

.inline-edit-input {
  width: 100%;
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--gray-300);
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.inline-edit-input:focus {
  outline: none;
  border-color: var(--primary);
}
</style>
