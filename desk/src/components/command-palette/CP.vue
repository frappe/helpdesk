<template>
  <DialogRoot :open="isOpen" @update:open="onOpenChange">
    <DialogPortal>
      <DialogOverlay
        class="fixed inset-0 z-[100] bg-black/30 dark:bg-black/60"
      />
      <DialogContent
        class="fixed left-1/2 top-[10%] z-[100] w-full max-w-[560px] -translate-x-1/2 overflow-hidden rounded-md bg-surface-base shadow-2xl ring-1 ring-black/[0.06] focus-visible:outline-none dark:ring-white/[0.08]"
        @open-auto-focus.prevent
        @escape-key-down.prevent="onEscape"
      >
        <DialogTitle class="sr-only">{{ __("Command Palette") }}</DialogTitle>

        <div class="flex items-center border-b border-outline-gray-1 px-1">
          <LucideSearch class="ms-3 size-4 shrink-0 text-ink-gray-4" />
          <button
            v-if="stepLabel"
            type="button"
            class="text-base-semibold ms-3 flex shrink-0 items-center gap-2 py-1 text-ink-gray-7"
            @click="back"
          >
            {{ stepLabel }}
            <LucideChevronRight class="size-3 text-ink-gray-4" />
          </button>
          <input
            ref="inputRef"
            :value="query"
            :placeholder="placeholder"
            class="w-full border-none bg-transparent py-3.5 pe-4 ps-3 text-base text-ink-gray-8 placeholder-ink-gray-4 outline-none ring-0 focus:outline-none focus:ring-0"
            autocomplete="off"
            spellcheck="false"
            @input="onQueryChange(($event.target as HTMLInputElement).value)"
            @keydown="onKeydown"
          />
          <kbd
            class="text-xs-medium me-3 shrink-0 rounded border border-outline-gray-2 px-1.5 py-1 text-ink-gray-4"
            :title="__('Close')"
          >
            esc
          </kbd>
        </div>

        <div ref="listRef" class="max-h-[380px] overflow-y-auto py-2">
          <template v-if="flatItems.length">
            <div
              v-for="group in groups"
              :key="group.title"
              class="mb-1 last:mb-0"
            >
              <div
                v-if="group.title"
                class="px-4 pb-1 pt-2 text-sm tracking-wider text-ink-gray-4"
              >
                {{ group.title }}
              </div>
              <div
                v-for="command in group.items"
                :key="`${group.title}:${command.id}`"
                class="cursor-pointer px-2"
                :data-active="activeCommand === command"
                @mousemove="onRowHover(command)"
                @click="run(command)"
              >
                <CPRow :command="command" :active="activeCommand === command" />
              </div>
            </div>
          </template>

          <div v-else class="flex flex-col items-center py-12 text-ink-gray-4">
            <component
              :is="
                isLoading
                  ? LucideLoaderCircle
                  : query
                  ? LucideSearchX
                  : LucideSearch
              "
              class="mb-2.5 size-8 opacity-40"
              :class="{ 'animate-spin': isLoading }"
            />
            <span class="text-base">
              <template v-if="isLoading">{{ __("Searching…") }}</template>
              <template v-else-if="query">
                {{ __('No results for "{0}"', [query]) }}
              </template>
              <template v-else>{{ __("No commands found") }}</template>
            </span>
          </div>
        </div>

        <div
          class="flex items-center gap-4 border-t border-outline-gray-1 px-4 py-2.5"
        >
          <span class="flex items-center gap-1.5 text-xs text-ink-gray-4">
            <span class="flex gap-1">
              <kbd :class="KEY_CHIP"><LucideArrowUp class="size-3" /></kbd>
              <kbd :class="KEY_CHIP"><LucideArrowDown class="size-3" /></kbd>
            </span>
            {{ __("Navigate") }}
          </span>
          <span class="flex items-center gap-1.5 text-xs text-ink-gray-4">
            <kbd :class="KEY_CHIP"><LucideCornerDownLeft class="size-3" /></kbd>
            {{ __("Select") }}
          </span>
          <span
            v-if="stepLabel"
            class="flex items-center gap-1.5 text-xs text-ink-gray-4"
          >
            <kbd :class="KEY_CHIP"><LucideDelete class="size-3" /></kbd>
            {{ __("Back") }}
          </span>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { useShortcut } from "frappe-ui";
import {
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "reka-ui";
import { computed, nextTick, ref, watch } from "vue";

import LucideArrowDown from "~icons/lucide/arrow-down";
import LucideArrowUp from "~icons/lucide/arrow-up";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideCornerDownLeft from "~icons/lucide/corner-down-left";
import LucideDelete from "~icons/lucide/delete";
import LucideLoaderCircle from "~icons/lucide/loader-circle";
import LucideSearch from "~icons/lucide/search";
import LucideSearchX from "~icons/lucide/search-x";
import CPRow from "./CPRow.vue";
import type { Command } from "./paletteTypes";
import {
  back,
  breadcrumb,
  closePalette,
  depth,
  flatItems,
  groups,
  isLoading,
  isOpen,
  onQueryChange,
  query,
  resetPalette,
  run,
} from "./useCommandPalette";

const KEY_CHIP =
  "rounded border border-outline-gray-2 p-0.5 text-[11px] font-medium";

const inputRef = ref<HTMLInputElement | null>(null);
const listRef = ref<HTMLElement | null>(null);
const activeIndex = ref(0);
const keyboardNav = ref(false);

// By identity, not id: a "Recent" row is a clone sharing its original's id.
const activeCommand = computed(() => flatItems.value[activeIndex.value]);
const stepLabel = computed(() => (depth.value ? breadcrumb.value.at(-1) : ""));
const placeholder = computed(() =>
  stepLabel.value ? __("Search…") : __("Search tickets or type a command…")
);

function onKeydown(event: KeyboardEvent) {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    moveActive(1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    moveActive(-1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    const command = flatItems.value[activeIndex.value];
    if (command) run(command);
  } else if (event.key === "Backspace" && !query.value && depth.value) {
    event.preventDefault();
    back();
  }
}

function moveActive(delta: number) {
  keyboardNav.value = true;
  const last = flatItems.value.length - 1;
  activeIndex.value = Math.min(Math.max(activeIndex.value + delta, 0), last);
  scrollActiveIntoView();
}

// Hover follows the pointer, not the list. Arrowing scrolls rows under a still
// cursor, and the resulting hover would drag the highlight back to the mouse.
function onRowHover(command: Command) {
  if (keyboardNav.value) {
    keyboardNav.value = false;
    return;
  }
  activeIndex.value = flatItems.value.indexOf(command);
}

/** Esc peels one layer at a time: clear the query, then the step, then close. */
function onEscape() {
  if (query.value) onQueryChange("");
  else if (depth.value) back();
  else closePalette();
}

function onOpenChange(open: boolean) {
  isOpen.value = open;
}

function scrollActiveIntoView() {
  nextTick(() => {
    listRef.value
      ?.querySelector('[data-active="true"]')
      ?.scrollIntoView({ block: "nearest" });
  });
}

// A changed result set invalidates the highlight position.
watch(groups, () => (activeIndex.value = 0));

// Every close path, not just onOpenChange: running a command sets isOpen
// directly, which is how a drill-down survived into the next open.
watch(isOpen, (open) => {
  if (!open) {
    resetPalette();
    return;
  }
  activeIndex.value = 0;
  nextTick(() => inputRef.value?.focus());
});

// Drilling into a sub-list swaps the whole list out; refocus for the next query.
watch(depth, () => nextTick(() => inputRef.value?.focus()));

// frappe-ui's useShortcut, not the local one: the local `disableShortcuts()`
// suppresses every binding while focus is in an input or inside [role=dialog],
// so Cmd+K couldn't open from a filter box nor close the palette once open.
// ProseMirror keeps its own Mod-k (insert link), so bow out there.
useShortcut({
  key: "k",
  ctrl: true,
  description: __("Open command palette"),
  group: __("General"),
  allowInInput: true,
  allowInDialog: true,
  condition: () => !document.activeElement?.closest?.(".ProseMirror"),
  handler: () => (isOpen.value = !isOpen.value),
});
</script>
