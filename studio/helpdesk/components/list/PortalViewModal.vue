<template>
  <Dialog
    v-model:open="open"
    :title="isRename ? __('Rename view') : __('Save as new view')"
    :actions="[
      {
        label: isRename ? __('Save') : __('Create'),
        variant: 'solid',
        disabled: !label.trim(),
        onClick: () => emit('submit'),
      },
    ]"
  >
    <FormControl
      v-model="label"
      type="text"
      :label="__('Name')"
      :placeholder="__('My open tickets')"
      autocomplete="off"
      @keyup.enter="label.trim() && emit('submit')"
    />
    <div class="mt-4">
      <div class="mb-1.5 text-base text-ink-gray-5">{{ __("Icon") }}</div>
      <div class="flex items-center gap-2">
        <!-- The icon list cannot show the emoji the desk's picker stored. -->
        <div
          v-if="isEmojiIcon"
          class="grid size-7 shrink-0 place-items-center rounded-4 bg-surface-gray-3 text-base leading-none"
          :title="__('Current icon')"
        >
          {{ icon }}
        </div>
        <IconPicker
          v-model="icon"
          :max-icons="1000"
          class="flex-1"
          :placeholder="
            isEmojiIcon
              ? __('Replace with an icon...')
              : __('Select an icon...')
          "
        />
      </div>
    </div>
    <p v-if="!isRename" class="mt-4 text-p-sm text-ink-gray-6">
      {{ __("Saves the filters, sort order and columns currently on screen.") }}
    </p>
  </Dialog>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Dialog, FormControl } from "frappe-ui";
import { IconPicker } from "frappe-ui/experimental";
import { __ } from "@helpdesk/shared/translation";
import { isEmoji } from "@helpdesk/shared/utils";

const props = withDefaults(defineProps<{ mode?: "create" | "rename" }>(), {
  mode: "create",
});
const emit = defineEmits<{ submit: [] }>();

const open = defineModel<boolean>("open", { default: false });
const label = defineModel<string>("label", { default: "" });
const icon = defineModel<string>("icon", { default: "" });

const isRename = computed(() => props.mode === "rename");
const isEmojiIcon = computed(() => isEmoji(icon.value));
</script>
