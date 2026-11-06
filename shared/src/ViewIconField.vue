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
      <IconPicker v-model="pickerIcon">
        <Button
          :icon-left="PickedIcon"
          :label="
            isEmojiIcon
              ? __('Replace with an icon...')
              : pickerIcon
              ? __('Change icon')
              : __('Select an icon...')
          "
        />
      </IconPicker>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from "vue";
import { Button } from "frappe-ui";
import Icon from "./Icon.vue";
import IconPicker from "./IconPicker.vue";
import { __ } from "./translation";
import { isEmoji } from "./utils";

const icon = defineModel<string>({ default: "" });

// Keep a legacy emoji out of the picker until replaced.
const isEmojiIcon = computed(() => isEmoji(icon.value));
const pickerIcon = computed({
  get: () => {
    if (isEmojiIcon.value || !icon.value) return "";
    // Views saved by the old picker hold bare names, such as `ticket`.
    return icon.value.startsWith("lucide-")
      ? icon.value
      : `lucide-${icon.value}`;
  },
  set: (value) => (icon.value = value || ""),
});
const PickedIcon = (attrs: Record<string, unknown>) =>
  h(Icon, { ...attrs, icon: pickerIcon.value || "lucide-plus" });
</script>
