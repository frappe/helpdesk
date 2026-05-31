<template>
  <Dialog
    v-model="modelValue"
    :options="{ size: 'xl' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <div class="text-lg font-semibold">{{ name }}</div>
        <div class="text-sm text-gray-500">Task details would be loaded here</div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{
  modelValue: boolean;
  name: string;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  'task-updated': [];
}>();

const modelValue = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
});

function handleUpdate(): void {
  emit('task-updated');
  modelValue.value = false;
}
</script>
