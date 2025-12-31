<template>
  <Dialog
    v-model="open"
    :options="{ title: __('Keyboard Shortcuts'), size: '4xl' }"
  >
    <template #body-content>
      <div class="w-full grid grid-cols-2 gap-10 py-1 shortcutsModal">
        <div
          v-for="group in shortcutGroups"
          :key="group.title"
          class="pb-4"
          :class="!group.hideBorder && 'border-b border-outline-gray-2'"
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
                  class="bg-surface-gray-2 border border-outline-gray-2 text-xs rounded-sm text-ink-gray-8 shadow-sm min-w-5 h-5 flex items-center justify-center"
                  :class="[
                    ![metaIcon, shiftKey].includes(key) && 'w-5 ',
                    key === shiftKey && '!px-2',
                  ]"
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
import { useDevice } from "@/composables/device";
import { useShortcut } from "@/composables/shortcuts";
import { isCustomerPortal } from "@/utils";
import { Dialog } from "frappe-ui";
import { computed, onMounted } from "vue";
import { __ } from "@/translation";

const props = defineProps({
  modelValue: Boolean,
});
const emit = defineEmits(["update:modelValue"]);
const open = defineModel<boolean>();

const { metaIcon } = useDevice();

// const shiftKey = "⇧";
const shiftKey = "Shift";

interface Shortcut {
  keys: string[];
  description: string;
}

interface ShortcutGroup {
  title: string;
  shortcuts: Shortcut[];
  hideBorder?: boolean;
}

const shortcutGroups = computed<ShortcutGroup[]>(() => [
  {
    title: __("General"),
    shortcuts: [
      { keys: [metaIcon, "K"], description: __("Open command palette") },
      { keys: [metaIcon, ","], description: __("Open settings") },
      { keys: [metaIcon, "/"], description: __("Show keyboard shortcuts") },
      { keys: [metaIcon, "H"], description: __("Open help") },
    ],
  },
  {
    title: __("Ticket Management"),
    shortcuts: [
      { keys: ["T"], description: __("Change ticket type") },
      { keys: ["P"], description: __("Change priority") },
      { keys: [shiftKey, "T"], description: __("Change team") },
      { keys: ["A"], description: __("Assign ticket") },
      { keys: ["S"], description: __("Change status") },
      { keys: [metaIcon, "."], description: __("Copy ticket id") },
      { keys: [metaIcon, shiftKey, "."], description: __("Copy ticket URL") },
    ],
  },
  {
    title: __("Communication"),
    shortcuts: [
      { keys: ["R"], description: __("Open reply box") },
      { keys: ["C"], description: __("Open comment box") },
    ],
    hideBorder: true,
  },
  {
    title: __("Navigation"),
    shortcuts: [
      { keys: [shiftKey, ">"], description: __("Next ticket") },
      { keys: [shiftKey, "<"], description: __("Previous ticket") },
    ],
    hideBorder: true,
  },
]);

onMounted(() => {
  if (isCustomerPortal.value) return;
  useShortcut({ key: "/", meta: true }, () => {
    open.value = !open.value;
  });
});
</script>
<style>
/* Hack to remove focus ring from buttons in shortcuts modal */
.bg-surface-modal:has(.shortcutsModal) button {
  @apply focus-visible:ring-0;
}
</style>
