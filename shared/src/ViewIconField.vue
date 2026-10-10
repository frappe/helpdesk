<template>
  <div>
    <div class="mb-1.5 text-base text-ink-gray-5">{{ __("Icon") }}</div>
    <div class="flex items-center gap-2">
      <div
        v-if="isEmojiIcon"
        class="grid size-7 shrink-0 place-items-center rounded-4 bg-surface-gray-3 text-base leading-none"
        :title="__('Current icon')"
      >
        {{ icon }}
      </div>
      <IconPicker
        v-model="pickerIcon"
        :max-icons="1000"
        class="flex-1"
        :placeholder="
          isEmojiIcon ? __('Replace with an icon...') : __('Select an icon...')
        "
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { IconPicker } from "frappe-ui/experimental";
import { __ } from "./translation";
import { isEmoji } from "./utils";

const icon = defineModel<string>({ default: "" });

// IconPicker is lucide-only and seeds its search from the value, so an emoji
// from an older view is kept out of it. A no-op edit keeps the emoji; picking
// an icon replaces it.
const isEmojiIcon = computed(() => isEmoji(icon.value));
const pickerIcon = computed({
  get: () => (isEmojiIcon.value ? "" : icon.value),
  set: (value) => (icon.value = value || ""),
});
</script>
