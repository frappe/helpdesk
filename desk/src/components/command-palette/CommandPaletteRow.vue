<template>
  <div
    class="flex w-full min-w-0 items-center rounded px-2 py-2 text-sm text-ink-gray-8"
    :class="{ 'bg-surface-gray-2': active }"
  >
    <span
      v-if="command.dotClass"
      class="me-2.5 size-2 shrink-0 rounded-full bg-current"
      :class="command.dotClass"
    />
    <component
      :is="command.icon"
      v-else-if="command.icon"
      v-bind="command.iconProps"
      class="me-2.5 size-3.5 shrink-0"
      :class="active ? 'text-ink-gray-7' : 'text-ink-gray-5'"
    />

    <span
      class="min-w-0 flex-1 overflow-hidden text-ellipsis whitespace-nowrap"
    >
      {{ command.title }}
    </span>

    <span v-if="command.subtitle" class="ms-3 shrink-0 text-xs text-ink-gray-4">
      {{ command.subtitle }}
    </span>
    <LucideCheck
      v-if="command.checked"
      class="ms-3 size-3.5 shrink-0 text-ink-gray-7"
    />
    <ShortcutKey
      v-if="command.hint"
      :keys="shortcutKeys"
      class="ms-3 shrink-0"
    />
    <LucideChevronRight
      v-if="command.children"
      class="ms-2 size-3.5 shrink-0 text-ink-gray-4"
    />
  </div>
</template>

<script setup lang="ts">
import ShortcutKey from "@/components/ShortcutKey.vue";
import { useDevice } from "@/composables";
import { computed } from "vue";
import LucideCheck from "~icons/lucide/check";
import LucideChevronRight from "~icons/lucide/chevron-right";
import type { Command } from "./paletteTypes";

const props = defineProps<{
  command: Command;
  active: boolean;
}>();

const { metaIcon } = useDevice();

/** "Mod+Shift+." -> "⌘ Shift ." — ShortcutKey caps each space-separated key. */
const shortcutKeys = computed(() =>
  (props.command.hint ?? "")
    .split("+")
    .map((key) => (key.toLowerCase() === "mod" ? metaIcon : key))
    .join(" ")
);
</script>
