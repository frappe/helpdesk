<template>
  <Select
    v-if="config.control === 'select'"
    class="w-full"
    variant="ghost"
    :model-value="(modelValue as string)"
    :options="options"
    :placeholder="placeholder"
    @update:model-value="emit('update:modelValue', $event as string)"
  />
  <Combobox
    v-else-if="config.control === 'combobox'"
    class="w-full"
    variant="ghost"
    trigger="button"
    :model-value="(modelValue as string)"
    :options="options"
    :placeholder="placeholder"
    @update:model-value="emit('update:modelValue', $event as string)"
    @update:query="emit('search', $event)"
  >
    <template v-if="type === 'Assign Agent'" #item-prefix="{ item }">
      <Avatar size="xs" :image="item.image" :label="item.label" />
    </template>
  </Combobox>
  <MultiSelect
    v-else-if="config.control === 'multiselect'"
    class="w-full"
    variant="ghost"
    :model-value="(modelValue as string[])"
    :options="options"
    :placeholder="__('Select tags')"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <template #item-prefix="{ item }">
      <span
        class="size-2.5 shrink-0 rounded-full"
        :class="colorToken(item.color)"
      />
    </template>
    <template #summary="{ selectedOptions }">
      <span
        v-if="selectedOptions.length"
        class="flex items-center gap-1.5 truncate"
      >
        <TagChip
          v-for="option in (selectedOptions as ActionOption[]).slice(0, 3)"
          :key="option.value"
          :tag="option.label"
          :color="colorToken(option.color)"
        />
        <span v-if="selectedOptions.length > 3" class="text-ink-gray-5">
          +{{ selectedOptions.length - 3 }}
        </span>
      </span>
      <span v-else>{{ __("Select tags") }}</span>
    </template>
    <!-- Custom summary renders its own dots; hide the default prefix so it adds no gap -->
    <template #prefix>
      <span class="hidden" />
    </template>
  </MultiSelect>
  <Editor
    v-else-if="config.control === 'editor'"
    class="w-full"
    :model-value="(modelValue as string)"
    :extensions="editorExtensions"
    :placeholder="__('Internal note. Type / for commands')"
    @update:model-value="emit('update:modelValue', $event ?? '')"
  >
    <template #default>
      <EditorContent
        class="prose prose-v3 [--prose-font-size:14px] min-h-8 max-h-30 w-full max-w-full overflow-auto rounded-4 bg-surface-gray-1 px-2 py-1.5 text-ink-gray-7 focus:ring-0"
      />
    </template>
  </Editor>
  <span
    v-else-if="config.hint"
    class="flex items-center px-2 text-base text-ink-gray-7 cursor-default"
  >
    {{ config.hint }}
  </span>
</template>

<script setup lang="ts">
import { buildEditorExtensions } from "@/components/editor/config";
import TagChip from "@/components/tag/TagChip.vue";
import { colorToken } from "@/composables/useTags";
import { __ } from "@/translation";
import { SavedReplyActionType } from "@/types";
import { Avatar, Combobox, MultiSelect, Select } from "frappe-ui";
import { Editor, EditorContent } from "frappe-ui/editor";
import { computed } from "vue";
import { ACTION_TYPES, type ActionOption } from "./actionTypes";

const props = defineProps<{
  type: SavedReplyActionType;
  modelValue: string | string[];
  options: ActionOption[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string | string[]];
  search: [query: string];
}>();

const config = computed(() => ACTION_TYPES[props.type]);
const placeholder = computed(() =>
  __("Select {0}", (config.value.fieldname || __("a value")).toLowerCase())
);
// Slash commands ship with RichTextKit, so "/" works without a toolbar.
const editorExtensions = buildEditorExtensions();
</script>
