<template>
  <DialogRoot :open="isOpen" @update:open="onOpenChange">
    <DialogPortal>
      <DialogOverlay
        class="palette-overlay fixed inset-0 z-[100] bg-black/30 dark:bg-black/60"
      />
      <DialogContent
        class="palette-content fixed left-1/2 top-[10%] z-[100] w-full max-w-[640px] -translate-x-1/2 overflow-hidden rounded-md bg-surface-base shadow-2xl ring-1 ring-black/[0.06] focus-visible:outline-none dark:ring-white/[0.08]"
        @open-auto-focus.prevent
        @close-auto-focus.prevent="restoreFocus"
        @escape-key-down.prevent="onEscape"
        @keydown="onKeydown"
      >
        <DialogTitle class="sr-only">{{ __("Command Palette") }}</DialogTitle>

        <!-- Collapses to zero height on dismiss, so the input glides up. -->
        <Transition name="chip">
          <div v-if="context" class="chip-row grid">
            <div class="overflow-hidden">
              <!-- Not a button: removal is backspace-only, advertised by esc's label. -->
              <Badge class="chip mx-4 mt-3 max-w-[30%]">
                <span class="shrink-0 text-ink-gray-7">{{
                  context.label
                }}</span>
                <span class="shrink-0 text-ink-gray-4">⋅</span>
                <span class="truncate leading-snug text-ink-gray-5">{{
                  context.title || __("Ticket")
                }}</span>
              </Badge>
            </div>
          </div>
        </Transition>

        <!-- px-2 + size sm puts the glass on the row icons' axis, and the caret on
             their titles' axis (8 + 8 = 16, 8 + 32 = 40). -->
        <div
          ref="inputWrapperRef"
          class="flex items-center border-b border-outline-gray-1 bg-surface-base px-2 py-2"
        >
          <button
            v-if="stepLabel"
            type="button"
            class="text-base-semibold ms-2 flex shrink-0 items-center gap-2 py-1 text-ink-gray-7"
            @click="back"
          >
            {{ stepLabel }}
            <LucideChevronRight class="size-3 text-ink-gray-4" />
          </button>
          <FormControl
            type="text"
            :model-value="query"
            :placeholder="placeholder"
            variant="ghost"
            size="sm"
            class="w-full !bg-surface-base"
            spellcheck="false"
            :aria-label="
              context
                ? __('Search commands for {0}', [context.label])
                : __('Search commands')
            "
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-list"
            :aria-activedescendant="activeOptionId"
            @update:model-value="onQueryChange"
          >
            <template #prefix>
              <LucideSearch class="size-3.5 shrink-0 text-ink-gray-4" />
            </template>
          </FormControl>
        </div>

        <!-- Announces what no row can: result count, and list changes under debounce. -->
        <div class="sr-only" aria-live="polite">{{ resultAnnouncement }}</div>

        <div
          id="command-palette-list"
          ref="listRef"
          role="listbox"
          class="max-h-[380px] min-h-[7rem] overflow-y-auto py-2"
        >
          <!-- Keyed by level: drill in/out fades, typing never re-keys. -->
          <Transition name="level" mode="out-in">
            <div :key="levelKey">
              <template v-if="flatItems.length">
                <div
                  v-for="(group, groupIndex) in renderGroups"
                  :key="`${groupIndex}:${group.title}`"
                  role="group"
                  :aria-label="group.title || __('Ticket')"
                >
                  <div
                    v-if="group.title"
                    class="px-4 pb-1 pt-2 text-xs font-medium text-ink-gray-4"
                  >
                    {{ group.title }}
                  </div>
                  <div
                    v-for="row in group.items"
                    :id="optionId(row.index)"
                    :key="`${group.title}:${row.command.id}`"
                    role="option"
                    :aria-selected="row.index === activeIndex"
                    class="cursor-pointer px-2"
                    :data-active="row.index === activeIndex"
                    @mousemove="onRowHover(row.command)"
                    @click="run(row.command)"
                  >
                    <CommandPaletteRow
                      :command="row.command"
                      :active="row.index === activeIndex"
                    />
                  </div>
                </div>
              </template>

              <!-- presentation: a listbox must not hold a non-option child. -->
              <div
                v-else
                role="presentation"
                class="flex flex-col items-center py-12 text-ink-gray-4"
              >
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
                <span class="text-base">{{ emptyMessage }}</span>
              </div>
            </div>
          </Transition>
        </div>

        <div
          class="flex items-center gap-4 border-t border-outline-gray-1 px-4 py-2.5"
        >
          <span class="flex items-center gap-1.5 text-xs text-ink-gray-4">
            <ShortcutKey keys="↑ ↓" />
            {{ __("Navigate") }}
          </span>
          <span class="flex items-center gap-1.5 text-xs text-ink-gray-4">
            <ShortcutKey keys="↵" />
            {{ __("Select") }}
          </span>
          <!-- No ⌫ hint for the chip: esc's label already says "Remove context". -->
          <span
            v-if="stepLabel"
            class="flex items-center gap-1.5 text-xs text-ink-gray-4"
          >
            <ShortcutKey keys="⌫" />
            {{ __("Back") }}
          </span>
          <span
            class="ms-auto flex items-center gap-1.5 text-xs text-ink-gray-4"
          >
            <ShortcutKey keys="esc" />
            {{ escapeLabel }}
          </span>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Badge, FormControl, useShortcut } from "frappe-ui";
import {
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "reka-ui";
import { computed, nextTick, ref, watch } from "vue";

import ShortcutKey from "@/components/ShortcutKey.vue";
import LucideChevronRight from "~icons/lucide/chevron-right";
import LucideLoaderCircle from "~icons/lucide/loader-circle";
import LucideSearch from "~icons/lucide/search";
import LucideSearchX from "~icons/lucide/search-x";
import CommandPaletteRow from "./CommandPaletteRow.vue";
import type { Command } from "./paletteTypes";
import {
  back,
  breadcrumb,
  closePalette,
  context,
  depth,
  dismissContext,
  flatItems,
  groups,
  isLoading,
  isOpen,
  isPaletteAvailable,
  onQueryChange,
  openPalette,
  query,
  resetPalette,
  run,
} from "./useCommandPalette";

// FormControl doesn't expose its native input, so we grab it from the DOM.
const inputWrapperRef = ref<HTMLElement | null>(null);
const inputRef = computed(
  () => inputWrapperRef.value?.querySelector("input") ?? null
);
const listRef = ref<HTMLElement | null>(null);
const activeIndex = ref(0);
const keyboardNav = ref(false);
let focusBeforeOpen: HTMLElement | null = null;

let activeRow: Command | null = null;

function rememberActive() {
  activeRow = flatItems.value[activeIndex.value] ?? null;
}

/** Rows paired with their flat index — highlighting compares indexes, not
 * object identity, which a "Recent" clone shares with its original. */
const renderGroups = computed(() => {
  let index = 0;
  return groups.value.map((group) => ({
    title: group.title,
    items: group.items.map((command) => ({ command, index: index++ })),
  }));
});

const optionId = (index: number) => `command-palette-option-${index}`;
const activeOptionId = computed(() =>
  flatItems.value.length ? optionId(activeIndex.value) : undefined
);

/** Per-level: an empty drill-down is not "No commands found". */
const emptyMessage = computed(() => {
  if (isLoading.value) return __("Searching…");
  if (query.value) return __('No results for "{0}"', query.value);
  if (stepLabel.value) return __("Nothing left in {0}", stepLabel.value);
  return __("No commands found");
});

const resultAnnouncement = computed(() => {
  if (isLoading.value) return __("Searching…");
  if (!flatItems.value.length) return emptyMessage.value;
  return __("{0} results", String(flatItems.value.length));
});

const stepLabel = computed(() => (depth.value ? breadcrumb.value.at(-1) : ""));

// Re-keys only on level/chip changes, never on typing.
const levelKey = computed(() => `${depth.value}:${context.value ? "c" : ""}`);
// Esc peels one layer at a time, so the label tracks what it will actually do.
const escapeLabel = computed(() => {
  if (query.value) return __("Clear");
  if (stepLabel.value) return __("Back");
  return context.value ? __("Remove context") : __("Close");
});
const placeholder = computed(() =>
  stepLabel.value ? __("Search…") : __("Search tickets or type a command…")
);

/** Bound to the dialog, not the input, so keys still work with focus on the back
 * button. Enter on a button must not double up with its own click. */
function onKeydown(event: KeyboardEvent) {
  const onButton = (event.target as HTMLElement | null)?.closest?.("button");
  if (event.key === "Enter" && onButton) return;
  // Ctrl+N/P are what readline-shaped hands reach for, and Raycast honours them.
  const down =
    event.key === "ArrowDown" || (event.ctrlKey && event.key === "n");
  const up = event.key === "ArrowUp" || (event.ctrlKey && event.key === "p");
  if (down) {
    event.preventDefault();
    moveActive(1);
  } else if (up) {
    event.preventDefault();
    moveActive(-1);
  } else if (event.key === "Home") {
    event.preventDefault();
    setActive(0);
  } else if (event.key === "End") {
    event.preventDefault();
    setActive(flatItems.value.length - 1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    const command = flatItems.value[activeIndex.value];
    if (command) run(command);
  } else if (
    event.key === "ArrowRight" &&
    !(event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) &&
    caretAtEnd()
  ) {
    // → drills in, mirroring ⌫ back — only at the caret's end so editing stays
    // native, and never on childless rows: running is Enter's job.
    const command = flatItems.value[activeIndex.value];
    if (command?.children) {
      event.preventDefault();
      run(command);
    }
  } else if (event.key === "Backspace" && !query.value) {
    // One layer per press, outermost last: step, then context.
    if (depth.value) {
      event.preventDefault();
      back();
    } else if (context.value) {
      event.preventDefault();
      dismissContext();
    }
  }
}

function moveActive(delta: number) {
  setActive(activeIndex.value + delta);
}

function caretAtEnd(): boolean {
  const input = inputRef.value;
  return (
    !!input &&
    input.selectionStart === input.selectionEnd &&
    input.selectionEnd === input.value.length
  );
}

function setActive(index: number) {
  keyboardNav.value = true;
  const last = flatItems.value.length - 1;
  activeIndex.value = Math.min(Math.max(index, 0), last);
  rememberActive();
  scrollActiveIntoView();
}

// Arrowing scrolls rows under a still cursor; that hover must not steal the highlight.
function onRowHover(command: Command) {
  if (keyboardNav.value) {
    keyboardNav.value = false;
    return;
  }
  activeIndex.value = flatItems.value.indexOf(command);
  rememberActive();
}

/**
 * Esc peels one layer at a time: the query, then the step, then the context,
 * then close.
 */
function onEscape() {
  if (query.value) onQueryChange("");
  else if (depth.value) back();
  else if (context.value) dismissContext();
  else closePalette();
}

function onOpenChange(open: boolean) {
  isOpen.value = open;
}

/** Only when the close left focus nowhere — a command's own focus move (saved
 * reply → composer) must win. */
function restoreFocus() {
  const target = focusBeforeOpen;
  focusBeforeOpen = null;
  if (!target?.isConnected) return;
  if (document.activeElement !== document.body) return;
  target.focus();
}

function scrollActiveIntoView() {
  nextTick(() => {
    listRef.value
      ?.querySelector('[data-active="true"]')
      ?.scrollIntoView({ block: "nearest" });
  });
}

// Late search results rebuild `groups`; follow the highlighted row to its new
// index or Enter runs whatever landed on top. Matched on group+id — recomputes
// re-create every object, and a "Recent" clone shares its original's id.
watch(groups, () => {
  const index = activeRow
    ? flatItems.value.findIndex(
        (command) =>
          command.id === activeRow!.id && command.group === activeRow!.group
      )
    : -1;
  activeIndex.value = Math.max(index, 0);
  rememberActive();
});

// Reset on open, not close — resetting on close revived the dismissed chip
// mid-fade. Close-side focus restore lives in @close-auto-focus, which fires
// after the exit animation, when a command's own focus move is known.
watch(isOpen, (open) => {
  if (!open) return;
  resetPalette();
  // No DialogTrigger, so nothing restores focus on its own.
  focusBeforeOpen = document.activeElement as HTMLElement | null;
  activeIndex.value = 0;
  rememberActive();
  nextTick(() => inputRef.value?.focus());
});

// Drilling into a sub-list swaps the whole list out; refocus for the next query.
watch(depth, () => nextTick(() => inputRef.value?.focus()));

// frappe-ui's useShortcut: the local one suppresses bindings in inputs and
// dialogs, so Cmd+K couldn't open from a filter box. ProseMirror keeps its own
// Mod-k (insert link), so bow out there.
useShortcut({
  key: "k",
  ctrl: true,
  description: __("Open command palette"),
  group: __("General"),
  allowInInput: true,
  allowInDialog: true,
  condition: () =>
    isPaletteAvailable.value &&
    !document.activeElement?.closest?.(".ProseMirror"),
  handler: () => (isOpen.value ? closePalette() : openPalette()),
});
</script>

<style scoped>
/* Native inputs fall back to the OS "Field" color (white) unless cleared explicitly. */
:deep(input[data-slot="control"]) {
  background-color: transparent;
}

/* Open carries the scale and lift; close is a plain fade so dismissal feels fast. */
.palette-content[data-state="open"] {
  animation: palette-in 160ms cubic-bezier(0.16, 1, 0.3, 1);
}

.palette-content[data-state="closed"] {
  animation: palette-out 110ms ease-in;
}

.palette-overlay[data-state="open"] {
  animation: fade-in 160ms ease-out;
}

.palette-overlay[data-state="closed"] {
  animation: fade-out 110ms ease-in;
}

@keyframes palette-in {
  from {
    opacity: 0;
    transform: translate(-50%, -6px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0) scale(1);
  }
}

@keyframes palette-out {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fade-out {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

/* grid-template-rows animates to intrinsic height; max-height guesswork cannot. */
.chip-row {
  grid-template-rows: 1fr;
  transition: grid-template-rows 180ms cubic-bezier(0.16, 1, 0.3, 1);
}

.chip-enter-active .chip,
.chip-leave-active .chip {
  transition: opacity 140ms ease, transform 180ms cubic-bezier(0.16, 1, 0.3, 1);
}

.chip-enter-from,
.chip-leave-to {
  grid-template-rows: 0fr;
}

.chip-enter-from .chip,
.chip-leave-to .chip {
  opacity: 0;
  transform: translateY(-4px) scale(0.96);
}

/* Enter-only: a leave fade kept old rows visible while Enter targeted the new
   level, so a fast double-Enter fired a command the user couldn't see. */
.level-enter-active {
  transition: opacity 100ms ease, transform 100ms ease;
}

.level-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

@media (prefers-reduced-motion: reduce) {
  .palette-content,
  .palette-overlay,
  .chip-row,
  .chip,
  .level-enter-active {
    animation: none !important;
    transition: none !important;
  }
}
</style>
