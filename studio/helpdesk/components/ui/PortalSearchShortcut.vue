<template>
  <span ref="root" class="contents">
    <ShortcutKey
      v-if="!hideKey"
      class="[@media(pointer:coarse)]:hidden"
      size="sm"
      keys="/"
    />
  </span>
</template>

<script setup lang="ts">
import { useKeyboardShortcut } from "frappe-ui";
import { ref } from "vue";
import ShortcutKey from "@helpdesk/shared/ShortcutKey.vue";

// A search box's suffix: "/" focuses the input it sits in. Page scripts run
// outside component setup, so they can't register the shortcut themselves.
const props = defineProps<{ description: string; hideKey?: boolean }>();

const root = ref<HTMLElement | null>(null);

useKeyboardShortcut({
  combo: "Slash",
  description: props.description,
  handler: () => {
    let box = root.value?.parentElement;
    while (box && !box.querySelector("input")) box = box.parentElement;
    box?.querySelector("input")?.focus();
  },
});
</script>
