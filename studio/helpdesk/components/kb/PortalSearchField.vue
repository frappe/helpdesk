<template>
  <div
    class="flex h-[34px] w-full cursor-text items-center gap-[13px] rounded-4 border border-[--surface-gray-2] bg-surface-gray-2 pl-2.5 pr-0.5 transition-colors hover:border-outline-elevation-2 hover:bg-surface-gray-3 focus-within:border-outline-gray-4 focus-within:bg-surface-base focus-within:shadow-sm hover:focus-within:border-outline-gray-4 hover:focus-within:bg-surface-base"
    @click="focus"
  >
    <!-- TextInput fixes its height and leaves a suffix 36px, too little for the shortcut.
         The box carries TextInput's subtle look itself, height and focus included, so the shortcut can come and go. -->
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

    <KeyboardShortcut
      v-if="!query"
      combo="Mod+K"
      class="shrink-0 pr-2 text-ink-gray-4"
    />
  </div>
</template>

<script setup lang="ts">
// A search box that ⌘K focuses, for lists that filter as you type.
import { ref } from "vue";
import { KeyboardShortcut, useKeyboardShortcut } from "frappe-ui";
import { __ } from "@helpdesk/shared/translation";

const SEARCH_GLYPH =
  "M5.15332 0C7.99942 0 10.3066 2.30722 10.3066 5.15332C10.3066 6.42343 9.8458 7.58508 9.08398 8.4834L10.6836 10.082L11.54 10.9395L11.9688 11.3682L12.1836 11.582C12.3789 11.7773 12.3789 12.0948 12.1836 12.29C11.9883 12.4853 11.6708 12.4853 11.4756 12.29L11.2617 12.0752L10.833 11.6465L9.97559 10.79L8.36621 9.17969C7.48496 9.88382 6.36904 10.3066 5.15332 10.3066C2.30722 10.3066 0 7.99942 0 5.15332C0 2.30722 2.30722 0 5.15332 0ZM5.15332 1C2.8595 1 1 2.8595 1 5.15332C1 7.44714 2.8595 9.30664 5.15332 9.30664C7.44714 9.30664 9.30664 7.44714 9.30664 5.15332C9.30664 2.8595 7.44714 1 5.15332 1Z";

withDefaults(defineProps<{ placeholder?: string }>(), { placeholder: "" });

const query = defineModel<string>({ default: "" });
const input = ref<HTMLInputElement | null>(null);

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
