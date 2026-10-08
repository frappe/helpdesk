<template>
  <div class="flex flex-col gap-3">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">
        {{ __("Pinned categories") }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __(
            "Pinned categories will appear first on your knowledge base home page, in this order."
          )
        }}
      </span>
    </div>
    <div
      v-if="pinned.length"
      class="relative rounded-5 border border-outline-gray-2 px-3 py-1"
      @touchmove="(event) => drag && event.preventDefault()"
    >
      <TransitionGroup
        tag="div"
        move-class="transition-transform duration-150 ease-[cubic-bezier(0.2,0,0,1)] motion-reduce:transition-none"
      >
        <div
          v-for="(name, index) in pinned"
          :key="name"
          class="border-b border-outline-gray-1 last:border-b-0"
        >
          <div
            class="group flex h-11 touch-pan-y select-none items-center gap-2.5 rounded-4 pl-2 pr-1.5 sm:h-10"
            :class="
              drag?.name === name
                ? 'bg-surface-gray-2 [&>*]:invisible'
                : 'cursor-grab hover:bg-surface-gray-1'
            "
            @pointerdown="(event) => press(event, index)"
          >
            <span
              class="lucide-grip-vertical size-4 shrink-0 text-ink-gray-4"
            />
            <span
              :class="byName[name]?.icon || 'lucide-folder'"
              class="size-4 shrink-0 text-ink-gray-6"
            />
            <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
              {{ labelOf(name) }}
            </span>
            <span class="shrink-0 text-base text-ink-gray-6">
              {{ countOf(name) }}
            </span>
            <div
              class="pinned-category-menu opacity-0 focus-within:opacity-100 group-hover:opacity-100 has-[[aria-expanded=true]]:opacity-100 [@media(hover:none)]:opacity-100"
            >
              <Dropdown align="end" :options="rowOptions(index)">
                <Button
                  variant="ghost"
                  icon="lucide-more-horizontal"
                  :label="__('Options for {0}', [labelOf(name)])"
                />
              </Dropdown>
            </div>
          </div>
        </div>
      </TransitionGroup>
      <!-- The lifted copy lives outside the list, so the rows and the slot can all slide freely. -->
      <div
        v-if="drag"
        ref="lifted"
        class="pointer-events-none absolute inset-x-3 z-10 flex h-11 cursor-grabbing items-center gap-2.5 rounded-4 bg-surface-elevation-2 pl-2 pr-1.5 shadow-xl sm:h-10"
        :style="{ top: `${drag.top}px` }"
      >
        <span class="lucide-grip-vertical size-4 shrink-0 text-ink-gray-6" />
        <span
          :class="byName[drag.name]?.icon || 'lucide-folder'"
          class="size-4 shrink-0 text-ink-gray-6"
        />
        <span class="min-w-0 flex-1 truncate text-base text-ink-gray-8">
          {{ labelOf(drag.name) }}
        </span>
        <span class="shrink-0 text-base text-ink-gray-6">
          {{ countOf(drag.name) }}
        </span>
        <span class="size-7 shrink-0" />
      </div>
    </div>
    <div
      v-else
      class="rounded-5 border border-outline-gray-2 p-4 text-center text-p-base text-ink-gray-6"
    >
      {{
        __("No categories pinned. The home page will show all categories, A–Z.")
      }}
    </div>
    <div class="self-start">
      <MultiSelect
        :model-value="pinned"
        :options="categories"
        :placeholder="__('Search categories')"
        :empty-text="__('No categories found')"
        align="start"
        @update:model-value="choose"
      >
        <template #trigger>
          <Button
            variant="subtle"
            icon-left="lucide-pin"
            :label="__('Choose categories')"
          />
        </template>
        <template #footer="{ clear }">
          <div class="border-t border-outline-gray-1 p-1.5">
            <Button
              variant="ghost"
              :label="__('Unpin all')"
              :disabled="!pinned.length"
              @click="clear"
            />
          </div>
        </template>
      </MultiSelect>
    </div>
    <span class="sr-only" aria-live="polite">{{ announcement }}</span>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { Button, Dropdown, MultiSelect } from "frappe-ui";
import { computed, nextTick, onUnmounted, ref } from "vue";

type Category = { label: string; value: string; icon: string; count: number };

// A mouse drag starts past a few pixels; a touch drag after a short hold, unless the finger moves first.
const MOUSE_SLOP = 4;
const TOUCH_SLOP = 8;
const TOUCH_HOLD_MS = 200;
const SETTLE = { duration: 150, easing: "cubic-bezier(0.2, 0, 0, 1)" };

const props = defineProps<{ categories: Category[] }>();
const pinned = defineModel<string[]>({ required: true });

const byName = computed(() =>
  Object.fromEntries(props.categories.map((row) => [row.value, row]))
);

// Kept pins hold their place and new ones go to the end; only the list itself reorders.
function choose(values: string[]) {
  pinned.value = [
    ...pinned.value.filter((name) => values.includes(name)),
    ...values.filter((name) => !pinned.value.includes(name)),
  ];
}

function labelOf(name: string) {
  return byName.value[name]?.label || name;
}

function countOf(name: string) {
  const count = byName.value[name]?.count || 0;
  return count === 1 ? __("1 article") : __("{0} articles", [count]);
}

// Read out after a move, since the menu closes and the row changes place.
const announcement = ref("");

function announce(name: string) {
  announcement.value = __("{0} moved to position {1} of {2}", [
    labelOf(name),
    pinned.value.indexOf(name) + 1,
    pinned.value.length,
  ]);
}

function moveTo(name: string, index: number) {
  const next = pinned.value.filter((row) => row !== name);
  next.splice(index, 0, name);
  pinned.value = next;
}

function rowOptions(index: number) {
  const name = pinned.value[index];
  return [
    {
      label: __("Move up"),
      icon: "lucide-arrow-up",
      disabled: index === 0,
      onClick: () => (moveTo(name, index - 1), announce(name)),
    },
    {
      label: __("Move down"),
      icon: "lucide-arrow-down",
      disabled: index === pinned.value.length - 1,
      onClick: () => (moveTo(name, index + 1), announce(name)),
    },
    {
      label: __("Unpin"),
      icon: "lucide-pin-off",
      onClick: () =>
        (pinned.value = pinned.value.filter((row) => row !== name)),
    },
  ];
}

// The lifted row follows the pointer up and down; the others reorder around its slot as it passes.
const drag = ref<{ name: string; top: number } | null>(null);
const lifted = ref<HTMLElement | null>(null);
let pressed: {
  name: string;
  row: HTMLElement;
  startY: number;
  startTop: number;
  firstTop: number;
  rowHeight: number;
  before: string[];
  touch: boolean;
  timer?: number;
} | null = null;

function press(event: PointerEvent, index: number) {
  const target = event.target as HTMLElement;
  if (event.button !== 0 || target.closest(".pinned-category-menu")) return;
  // Measured on the wrapper, so the divider counts toward the row height.
  const row = event.currentTarget as HTMLElement;
  const wrapper = row.parentElement!;
  const firstTop = wrapper.offsetTop - index * wrapper.offsetHeight;
  pressed = {
    name: pinned.value[index],
    row,
    startY: event.clientY,
    startTop: wrapper.offsetTop,
    firstTop,
    rowHeight: wrapper.offsetHeight,
    before: [...pinned.value],
    touch: event.pointerType === "touch",
  };
  if (pressed.touch) pressed.timer = window.setTimeout(lift, TOUCH_HOLD_MS);
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
  window.addEventListener("pointercancel", cancel);
  window.addEventListener("keydown", onKeydown, true);
}

function lift() {
  if (pressed) drag.value = { name: pressed.name, top: pressed.startTop };
}

function onMove(event: PointerEvent) {
  if (!pressed) return;
  const moved = event.clientY - pressed.startY;
  if (!drag.value) {
    if (Math.abs(moved) <= (pressed.touch ? TOUCH_SLOP : MOUSE_SLOP)) return;
    if (pressed.touch) return stop();
    lift();
  }
  const last = pressed.firstTop + (pinned.value.length - 1) * pressed.rowHeight;
  const top = Math.min(
    Math.max(pressed.startTop + moved, pressed.firstTop),
    last
  );
  drag.value!.top = top;
  const over = Math.round((top - pressed.firstTop) / pressed.rowHeight);
  if (pinned.value[over] !== pressed.name) moveTo(pressed.name, over);
}

function onUp() {
  if (drag.value && pressed && pinned.value.join() !== pressed.before.join()) {
    announce(pressed.name);
  }
  stop();
}

function cancel() {
  if (drag.value && pressed) pinned.value = pressed.before;
  stop();
}

// Captured, so Escape cancels the drag without also closing the settings dialog.
function onKeydown(event: KeyboardEvent) {
  if (event.key !== "Escape" || !drag.value) return;
  event.stopPropagation();
  cancel();
}

function stop() {
  const row = drag.value ? pressed?.row : null;
  const style = lifted.value && getComputedStyle(lifted.value);
  const from = style && {
    top: lifted.value!.getBoundingClientRect().top,
    boxShadow: style.boxShadow,
    backgroundColor: style.backgroundColor,
  };
  clearTimeout(pressed?.timer);
  pressed = null;
  drag.value = null;
  window.removeEventListener("pointermove", onMove);
  window.removeEventListener("pointerup", onUp);
  window.removeEventListener("pointercancel", cancel);
  window.removeEventListener("keydown", onKeydown, true);
  if (row && from) settle(row, from);
}

// The dropped row eases from where it was let go into its slot, its lift fading as it lands.
async function settle(
  row: HTMLElement,
  from: { top: number; boxShadow: string; backgroundColor: string }
) {
  await nextTick();
  const offset = from.top - row.getBoundingClientRect().top;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  row.animate(
    [
      {
        transform: `translateY(${offset}px)`,
        boxShadow: from.boxShadow,
        backgroundColor: from.backgroundColor,
      },
      { transform: "none", boxShadow: "none", backgroundColor: "transparent" },
    ],
    SETTLE
  );
}

onUnmounted(stop);
</script>
