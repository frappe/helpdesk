<template>
  <div
    class="flex h-9 w-full min-w-0 items-center rounded px-2 text-sm text-ink-gray-8 leading-snug"
    :class="{ 'bg-surface-gray-2': active }"
  >
    <Avatar
      v-if="command.avatar"
      :image="command.avatar.image"
      :label="command.avatar.label"
      size="xs"
      class="me-2.5 shrink-0"
    />
    <!-- Boxed to the icon's 3.5 width, so a dot row's title lands on the same axis. -->
    <span
      v-else-if="command.dotClass"
      class="me-2.5 flex size-3.5 shrink-0 items-center justify-center"
    >
      <span class="size-2 rounded-full bg-current" :class="command.dotClass" />
    </span>
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
      <template v-for="(run, index) in runs" :key="index">
        <span v-if="run.match" class="font-medium text-ink-gray-9">{{
          run.text
        }}</span>
        <template v-else>{{ run.text }}</template>
      </template>
      <span v-if="command.titleSuffix" class="text-ink-gray-5">{{
        " " + command.titleSuffix
      }}</span>
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
import { Avatar } from "frappe-ui";
import { computed } from "vue";
import LucideCheck from "~icons/lucide/check";
import LucideChevronRight from "~icons/lucide/chevron-right";
import { titleRuns, type Command } from "./paletteTypes";

const props = defineProps<{
  command: Command;
  active: boolean;
}>();

const { metaIcon } = useDevice();

/** One unmatched run for every row without server highlighting. */
const runs = computed(() =>
  props.command.marked
    ? titleRuns(props.command.marked)
    : [{ text: props.command.title, match: false }]
);

/** "Mod+Shift+." -> "⌘ Shift ." — ShortcutKey caps each space-separated key. */
const shortcutKeys = computed(() =>
  (props.command.hint ?? "")
    .split("+")
    .map((key) => (key.toLowerCase() === "mod" ? metaIcon : key))
    .join(" ")
);
</script>
