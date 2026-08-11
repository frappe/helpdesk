<template>
  <Tooltip :text="value ? `${label}: ${value}` : label">
    <Badge class="bg-surface-base" theme="gray" variant="outline" size="lg">
      <template #prefix>
        <component :is="config.icon" class="size-3 shrink-0 text-ink-gray-6" />
      </template>
      <span class="flex min-w-0 items-center gap-1">
        <span v-if="value" class="shrink-0 text-ink-gray-6">{{ label }}</span>
        <span class="max-w-40 truncate text-ink-gray-8">{{
          value || label
        }}</span>
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
import { __ } from "@/translation";
import { SavedReplyAction } from "@/types";
import { Badge, Tooltip } from "frappe-ui";
import { computed } from "vue";
import LucideX from "~icons/lucide/x";

const props = defineProps<{
  action: SavedReplyAction;
}>();

const emit = defineEmits<{
  remove: [];
}>();

const config = computed(() => ACTION_TYPES[props.action.action_type]);
const label = computed(() => config.value.chipLabel);
// Empty for no-value actions like "Assign to Me"; the noun then stands alone
const value = computed(() => props.action.label || props.action.value);
</script>
