<template>
  <Combobox
    trigger="button"
    :disabled="!isEditable"
    :model-value="action.value"
    :options="pickerOptions"
    :placeholder="__('Select {0}', label.toLowerCase())"
    @update:model-value="pick($event as string)"
    @update:query="search(action.action_type, $event)"
  >
    <template #trigger="{ setOpen }">
      <!-- The anchor forwards its click to this element, so it has to be a plain
           one: Tooltip and Combobox both drop inherited attrs -->
      <div
        class="inline-flex"
        :role="isEditable ? 'button' : undefined"
        :tabindex="isEditable ? 0 : undefined"
        @keydown.enter.self.prevent="setOpen(true)"
      >
        <Tooltip :text="value ? `${label}: ${value}` : label">
          <Badge
            class="bg-surface-base transition-colors"
            :class="isEditable ? 'cursor-pointer hover:bg-surface-gray-2' : ''"
            theme="gray"
            variant="outline"
            size="lg"
          >
            <template #prefix>
              <component
                :is="config.icon"
                class="size-3 shrink-0 text-ink-gray-6"
              />
            </template>
            <span class="flex min-w-0 items-center gap-1">
              <span v-if="value" class="shrink-0 text-ink-gray-6">
                {{ label }}
              </span>
              <span class="max-w-40 truncate text-ink-gray-8">
                {{ value || label }}
              </span>
            </span>
            <template #suffix>
              <!-- Removing is not picking: the click stops here -->
              <button
                type="button"
                :aria-label="__('Remove {0}', label)"
                class="flex items-center rounded-sm text-ink-gray-6 transition-colors hover:text-ink-gray-9 focus-visible:ring-2 focus-visible:ring-outline-gray-3 mt-[1px]"
                @click.stop="emit('remove')"
                @pointerdown.stop
              >
                <LucideX class="size-3" />
              </button>
            </template>
          </Badge>
        </Tooltip>
      </div>
    </template>
  </Combobox>
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
  /** Values the other chips hold, so a repoint can't collide with them. */
  taken?: string[];
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

// A tag chip holds one tag, so it picks like the rest; no-value actions have
// nothing to pick
const isEditable = computed(() =>
  ["select", "combobox", "multiselect"].includes(config.value.control)
);

// Combobox takes string values; the shared options allow numbers too
const pickerOptions = computed(() =>
  valueOptions(props.action.action_type)
    .filter((option) => !props.taken?.includes(String(option.value)))
    .map((option) => ({
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
