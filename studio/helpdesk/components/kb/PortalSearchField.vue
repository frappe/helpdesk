<template>
  <div
    class="flex w-full cursor-text items-center gap-[13px] rounded-4 bg-surface-gray-2 py-0.5 pl-2.5 pr-0.5"
    @click="focus"
  >
    <!-- TextInput fixes its height and leaves a suffix 36px, too little for the shortcut chip. -->
    <div class="flex min-w-0 flex-1 items-center gap-2">
      <span class="relative size-4 shrink-0 overflow-hidden text-ink-gray-4">
        <svg
          viewBox="0 0 12.33 12.4365"
          fill="none"
          aria-hidden="true"
          class="absolute inset-[9.53%_13.07%_12.74%_9.86%]"
        >
          <path :d="SEARCH_GLYPH" fill="currentColor" />
        </svg>
      </span>
      <input
        ref="input"
        v-model="query"
        type="text"
        class="min-w-0 flex-1 border-0 bg-transparent p-0 text-[14px] leading-[1.15] tracking-[0.28px] text-ink-gray-8 placeholder:text-ink-gray-4 focus:shadow-none focus:outline-none focus:ring-0"
        :placeholder="placeholder"
      />
    </div>

    <span
      v-if="shortcutVariant === 'keys'"
      class="flex shrink-0 items-center gap-0.5 whitespace-nowrap border border-transparent px-[9px] py-1.5 text-[14px] leading-[1.15] tracking-[0.28px] text-ink-gray-4"
    >
      <span v-if="isMac" class="relative size-4 overflow-hidden">
        <svg
          viewBox="0 0 13 13"
          fill="none"
          aria-hidden="true"
          class="absolute inset-[9.38%]"
        >
          <path :d="COMMAND_GLYPH" fill="currentColor" />
        </svg>
      </span>
      <span v-else>Ctrl</span>
      <span>+K</span>
    </span>
    <span
      v-else
      class="shrink-0 whitespace-nowrap rounded-4 border border-outline-gray-2 bg-surface-gray-2 px-[9px] py-1.5 text-[14px] leading-[1.15] tracking-[0.28px] text-ink-gray-4"
    >
      {{ isMac ? "Cmd+k" : "Ctrl+K" }}
    </span>
  </div>
</template>

<script setup lang="ts">
// A search box that ⌘K focuses, for lists that filter as you type.
import { ref } from "vue";
import { useKeyboardShortcut } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

const SEARCH_GLYPH =
  "M5.15332 0C7.99942 0 10.3066 2.30722 10.3066 5.15332C10.3066 6.42343 9.8458 7.58508 9.08398 8.4834L10.6836 10.082L11.54 10.9395L11.9688 11.3682L12.1836 11.582C12.3789 11.7773 12.3789 12.0948 12.1836 12.29C11.9883 12.4853 11.6708 12.4853 11.4756 12.29L11.2617 12.0752L10.833 11.6465L9.97559 10.79L8.36621 9.17969C7.48496 9.88382 6.36904 10.3066 5.15332 10.3066C2.30722 10.3066 0 7.99942 0 5.15332C0 2.30722 2.30722 0 5.15332 0ZM5.15332 1C2.8595 1 1 2.8595 1 5.15332C1 7.44714 2.8595 9.30664 5.15332 9.30664C7.44714 9.30664 9.30664 7.44714 9.30664 5.15332C9.30664 2.8595 7.44714 1 5.15332 1Z";
const COMMAND_GLYPH =
  "M10.5 0C11.8807 0 13 1.11929 13 2.5C13 3.88071 11.8807 5 10.5 5H9V8H10.5C11.8807 8 13 9.11929 13 10.5C13 11.8807 11.8807 13 10.5 13C9.11929 13 8 11.8807 8 10.5V9H5V10.5C5 11.8807 3.88071 13 2.5 13C1.11929 13 0 11.8807 0 10.5C0 9.11929 1.11929 8 2.5 8H4V5H2.5C1.11929 5 0 3.88071 0 2.5C0 1.11929 1.11929 0 2.5 0C3.88071 0 5 1.11929 5 2.5V4H8V2.5C8 1.11929 9.11929 0 10.5 0ZM2.5 9C1.67157 9 1 9.67157 1 10.5C1 11.3284 1.67157 12 2.5 12C3.32843 12 4 11.3284 4 10.5V9H2.5ZM9 10.5C9 11.3284 9.67157 12 10.5 12C11.3284 12 12 11.3284 12 10.5C12 9.67157 11.3284 9 10.5 9H9V10.5ZM5 8H8V5H5V8ZM2.5 1C1.67157 1 1 1.67157 1 2.5C1 3.32843 1.67157 4 2.5 4H4V2.5C4 1.67157 3.32843 1 2.5 1ZM10.5 1C9.67157 1 9 1.67157 9 2.5V4H10.5C11.3284 4 12 3.32843 12 2.5C12 1.67157 11.3284 1 10.5 1Z";

withDefaults(
  defineProps<{
    placeholder?: string;
    /** "label" is one bordered chip, "keys" the bare keys. */
    shortcutVariant?: "label" | "keys";
  }>(),
  { placeholder: "", shortcutVariant: "label" }
);

const query = defineModel<string>({ default: "" });
const input = ref<HTMLInputElement | null>(null);
const isMac = /Mac/i.test(navigator.platform);

function focus() {
  input.value?.focus();
}

useKeyboardShortcut({
  combo: "Mod+K",
  description: __("Search articles"),
  handler: () => {
    focus();
    input.value?.select();
  },
});
</script>
