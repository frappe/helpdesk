<template>
  <Dialog
    v-model="open"
    :options="{ title: 'Keyboard Shortcuts', size: '4xl' }"
  >
    <template #body-content>
      <div v-focus class="w-full grid grid-cols-2 gap-10 py-1">
        <div
          v-for="group in shortcutGroups"
          :key="group.title"
          class="border-b border-outline-gray-2 pb-4"
        >
          <h2 class="text-lg font-semibold text-ink-gray-9 mb-4">
            {{ group.title }}
          </h2>
          <ul class="space-y-2">
            <li
              v-for="(shortcut, index) in group.shortcuts"
              :key="index"
              class="flex items-start justify-between gap-4"
            >
              <div class="text-ink-gray-7 text-base flex-1">
                {{ shortcut.description }}
              </div>
              <div class="flex space-x-1 gap-1 justify-end">
                <span
                  v-for="(key, kIndex) in shortcut.keys"
                  :key="kIndex"
                  class="px-2 py-0.5 bg-surface-gray-2 border border-outline-gray-2 text-xs rounded-sm font-mono text-ink-gray-8 shadow-sm"
                >
                  {{ key }}
                </span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Dialog } from "frappe-ui";
import { computed } from "vue";
import { useShortcut } from "@/composables/shortcuts";
import { useDevice } from "@/composables/device";

const props = defineProps({
  modelValue: Boolean,
});
const emit = defineEmits(["update:modelValue"]);

const { isMac, metaKey } = useDevice();

// const shiftKey = "⇧";
const shiftKey = "Shift";

interface Shortcut {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  title: string;
  shortcuts: Shortcut[];
}

const shortcutGroups = computed<ShortcutGroup[]>(() => [
  {
    title: "General",
    shortcuts: [
      { keys: [metaKey, "K"], description: "Open command palette" },
      { keys: [shiftKey, "?"], description: "Show keyboard shortcuts" },
      //     useShortcut({ key: ",", meta: true }, () => {
      // showSettingsModal.value = !showSettingsModal.value;
      //   });
      { keys: [metaKey, ","], description: "Open settings" },
    ],
  },
  {
    title: "Ticket Fields",
    shortcuts: [
      { keys: ["T"], description: "Change ticket type" },
      { keys: ["P"], description: "Change priority" },
      { keys: [shiftKey, "T"], description: "Change agent group" },
      { keys: ["A"], description: "Assign ticket" },
      { keys: ["S"], description: "Change status" },
    ],
  },
  {
    title: "Communication",
    shortcuts: [
      { keys: ["R"], description: "Open reply box" },
      { keys: ["C"], description: "Open comment box" },
    ],
  },
  {
    title: "Navigation",
    shortcuts: [
      { keys: [shiftKey, ">"], description: "Next ticket" },
      { keys: [shiftKey, "<"], description: "Previous ticket" },
    ],
  },
]);

const open = defineModel();

// Add shortcut to open/close the modal
useShortcut({ key: "?", shift: true }, () => {
  open.value = !open.value;
});
</script>
