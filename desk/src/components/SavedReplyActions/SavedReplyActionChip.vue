<template>
  <Tooltip :text="value ? `${label}: ${value}` : label">
    <Badge class="bg-surface-base" theme="gray" variant="outline" size="lg">
      <template #prefix>
        <component :is="config.icon" class="size-3 shrink-0 text-ink-gray-6" />
      </template>
      <span class="flex min-w-0 items-center gap-1">
        <span v-if="value" class="shrink-0 text-ink-gray-6">{{ label }}</span>
        <!-- The value doubles as the picker's trigger, so a routing action can
             be pointed somewhere else without re-picking the whole reply.
             Combobox over Select: its `#trigger` replaces the control outright,
             where Select's renders inside its own bordered button -->
        <Combobox
          v-if="isEditable"
          trigger="button"
          :model-value="action.value"
          :options="pickerOptions"
          :placeholder="__('Select {0}', label.toLowerCase())"
          @update:model-value="pick($event as string)"
          @update:query="search(action.action_type, $event)"
        >
          <template #trigger>
            <button
              type="button"
              class="max-w-40 cursor-pointer truncate text-start text-ink-gray-8 hover:text-ink-gray-5"
            >
              {{ value }}
            </button>
          </template>
        </Combobox>
        <span v-else class="max-w-40 truncate text-ink-gray-8">
          {{ value || label }}
        </span>
      </span>
      <template #suffix>
        <button
          type="button"
          :aria-label="__('Remove {0}', label)"
          class="flex items-center rounded-sm text-ink-gray-6 transition-colors hover:text-ink-gray-9 focus-visible:ring-2 focus-visible:ring-outline-gray-3 mt-[1px]"
          @click.stop="emit('remove')"
        >
          <LucideX class="size-3" />
        </button>
      </template>
    </Badge>
  </Tooltip>
</template>

<script setup lang="ts">
import { ACTION_TYPES } from "@/components/Settings/SavedReplies/components/actionTypes";
import { useSavedReplyActionOptions } from "@/composables/useSavedReplyActionOptions";
import { __ } from "@/translation";
import { SavedReplyAction } from "@/types";
import { Badge, Combobox, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideX from "~icons/lucide/x";

const props = defineProps<{
  action: SavedReplyAction;
}>();

const emit = defineEmits<{
  update: [action: SavedReplyAction];
  remove: [];
}>();

const { valueOptions, search } = useSavedReplyActionOptions();

const config = computed(() => ACTION_TYPES[props.action.action_type]);
const label = computed(() => config.value.chipLabel);
// Empty for no-value actions like "Assign to Me"; the noun then stands alone
const value = computed(() => props.action.label || props.action.value);

// Tags are one chip per tag over a multi-select, which a single picker can't
// express; no-value actions have nothing to pick
const isEditable = computed(() =>
  ["select", "combobox"].includes(config.value.control)
);

// Combobox takes string values; the shared options allow numbers too
const pickerOptions = computed(() =>
  valueOptions(props.action.action_type).map((option) => ({
    label: option.label,
    value: String(option.value),
  }))
);

/** `label` carries the display name (an agent's, not their id), so both move. */
function pick(picked: string) {
  const option = pickerOptions.value.find(
    (candidate) => candidate.value === picked
  );
  if (!option) return;
  emit("update", { ...props.action, value: option.value, label: option.label });
}
</script>
