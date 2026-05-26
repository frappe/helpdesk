<template>
  <div class="inline-flex items-center rounded-md bg-surface-gray-2 p-0.5">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      :class="[
        'flex items-center gap-1.5 rounded px-2 py-1 text-sm transition',
        modelValue === opt.value
          ? 'bg-surface-white text-ink-gray-9 shadow-sm'
          : 'text-ink-gray-6 hover:text-ink-gray-8',
      ]"
      :title="opt.label"
      @click="$emit('update:modelValue', opt.value)"
    >
      <FeatherIcon :name="opt.icon" class="h-3.5 w-3.5" />
      <span v-if="!hideLabel" class="hidden sm:inline">{{ opt.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { FeatherIcon } from "frappe-ui";
import { __ } from "@/translation";

defineProps<{
  modelValue: "list" | "group_by" | "kanban";
  hideLabel?: boolean;
}>();
defineEmits<{
  (e: "update:modelValue", value: "list" | "group_by" | "kanban"): void;
}>();

const options = [
  { value: "list", label: __("List"), icon: "list" },
  { value: "group_by", label: __("Group By"), icon: "layers" },
  { value: "kanban", label: __("Kanban"), icon: "columns" },
] as const;
</script>
