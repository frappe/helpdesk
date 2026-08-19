<template>
  <!-- Full-bleed white section, so the block reads as one box with a gray top
       and a white bottom rather than a card floating inside another card -->
  <div class="border-t border-outline-gray-1 bg-surface-base">
    <div class="flex h-8 items-center gap-1.5 ps-3.5 pe-1.5 text-sm">
      <LucideMessageSquare class="size-3 shrink-0 text-ink-gray-6" />
      <span class="shrink-0 text-ink-gray-6">{{ __("Comment") }}</span>
      <Button
        class="ms-auto shrink-0"
        variant="ghost"
        size="xs"
        icon="lucide-x"
        :label="__('Remove comment')"
        @click="emit('remove')"
      />
    </div>
    <Editor
      :model-value="action.value"
      :extensions="extensions"
      :placeholder="__('Comment')"
      @update:model-value="emit('update:value', $event ?? '')"
    >
      <template #default>
        <EditorContent
          class="prose prose-v3 [--prose-font-size:13px] max-w-none max-h-[140px] min-h-16 overflow-y-auto px-3.5 py-2"
        />
      </template>
    </Editor>
    <!-- Fixed height so the reset button appearing doesn't grow the footer -->
    <div
      class="flex h-9 items-center gap-2 ps-3.5 pe-1.5 pb-2 text-xs text-ink-gray-5"
    >
      <span class="cursor-default">
        {{ __("Visible to your team only, never sent to the customer.") }}
      </span>
      <Button
        v-if="isEdited"
        class="ms-auto"
        variant="ghost"
        size="sm"
        :label="__('Reset to default')"
        @click="emit('update:value', action.original_value ?? '')"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { buildEditorExtensions } from "@/components/editor/config";
import { useAgentStore } from "@/stores/agent";
import { __ } from "@/translation";
import { SavedReplyAction } from "@/types";
import { Button } from "frappe-ui";
import { Editor, EditorContent } from "frappe-ui/editor";
import { storeToRefs } from "pinia";
import { computed } from "vue";
import LucideMessageSquare from "~icons/lucide/message-square";

const props = defineProps<{
  action: SavedReplyAction;
}>();

const emit = defineEmits<{
  "update:value": [value: string];
  remove: [];
}>();

/** Only actions staged with the original text can report an edit. */
const isEdited = computed(
  () =>
    props.action.original_value !== undefined &&
    props.action.original_value !== props.action.value
);

// Same editor the Comment tab uses: rich text with @-mentions
const { dropdown: agentDropdown } = storeToRefs(useAgentStore());
const extensions = buildEditorExtensions({
  mentions: () =>
    (agentDropdown.value ?? []).map((a: { label: string; value: string }) => ({
      id: a.value,
      label: a.label,
    })),
});
</script>
