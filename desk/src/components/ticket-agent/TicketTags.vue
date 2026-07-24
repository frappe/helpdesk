<template>
  <!-- The color step is a sibling popover on the same anchor, so it opens
       exactly where the tag picker just closed, reading as an in-place
       content swap (Linear's create-label flow) -->
  <Popover v-model:open="colorPickerOpen" side="left" align="start">
    <!-- plain div anchor: MultiSelect's own root is display:contents,
         which would give the PopoverAnchor a zero rect -->
    <template #target>
      <div>
        <MultiSelect
          v-model="localTags"
          v-model:open="tagPickerOpen"
          :options="tagOptions"
          :loading="tagListResource.loading"
          :placeholder="__('Search or create tags')"
          side="left"
          @update:query="queryText = $event"
        >
          <template #trigger>
            <div class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
              <TagChip
                v-for="tag in headTags"
                :key="tag"
                :tag="tag"
                :color="tagColorToken(tag)"
              />
              <!-- the last chip and the trailing control (+ button or "+N
                   more" chip) form one flex item, so neither can wrap onto
                   a line of its own; new tags land at the end of localTags,
                   so the enter transition still plays on every freshly
                   added chip below the fold -->
              <div class="flex min-w-0 max-w-full items-center gap-1.5">
                <Transition name="tag-chip">
                  <TagChip
                    v-if="lastTag"
                    :key="lastTag"
                    :tag="lastTag"
                    :color="tagColorToken(lastTag)"
                  />
                </Transition>
                <Tooltip v-if="!hiddenTags.length" :text="__('Add')">
                  <!-- h-6 matches Badge size=lg so the row height never changes
                 when the first chip appears (no layout shift) -->
                  <button
                    v-if="!localTags.length"
                    class="inline-flex items-center text-base text-ink-gray-6 transition-[color,transform] duration-150 hover:text-ink-gray-8 active:scale-[0.96]"
                  >
                    + {{ __("Add") }}
                  </button>
                  <!-- with tags present, collapse to a ghost + icon -->
                  <button
                    v-else
                    class="inline-flex h-6 w-6 items-center justify-center rounded-full text-ink-gray-5 transition-[color,background-color,transform] duration-150 hover:bg-surface-gray-2 hover:text-ink-gray-7 active:scale-[0.96]"
                  >
                    <LucidePlus class="size-3.5" />
                  </button>
                </Tooltip>
              </div>
              <!-- collapsed tags: a separate wrap item (grouping it with the
                   last chip inflates the row's min-content width and blows
                   past the panel edge); it may wrap to its own line like any
                   chip. It's also the popover's click target, so the ghost +
                   above yields to it; hover lists the hidden names -->
              <Tooltip v-if="hiddenTags.length" :text="hiddenTags.join(', ')">
                <Badge
                  theme="gray"
                  variant="outline"
                  size="lg"
                  class="shrink-0 text-ink-gray-7 transition-colors duration-150 hover:bg-surface-gray-2"
                >
                  {{ __("+{0} more", String(hiddenTags.length)) }}
                </Badge>
              </Tooltip>
            </div>
          </template>
          <template #suffix>
            <ShortcutKey v-if="!queryText" keys="G" />
          </template>
          <template #item-prefix="{ item }">
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: colorToken(item.color) }"
            />
          </template>
          <template #empty>
            <span class="text-p-sm">
              {{ __("No tags yet, type to create one") }}
            </span>
          </template>
          <!-- The hidden marker scopes this picker's style overrides
               (see <style>); the popover is portaled so scoped styles
               can't reach it -->
          <template #footer>
            <span class="ticket-tags-marker hidden" aria-hidden="true" />
          </template>
        </MultiSelect>
      </div>
    </template>
    <div class="flex w-52 flex-col">
      <!-- live preview of the tag being created: the dot tracks the
           highlighted color -->
      <p
        class="flex items-center gap-2 border-b border-outline-gray-2 px-3 py-2 text-base text-ink-gray-8"
      >
        <span
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: TAG_COLORS[TAG_COLOR_NAMES[colorIndex]] }"
        />
        <span class="min-w-0 truncate">{{ pendingTag }}</span>
      </p>
      <div class="flex flex-col p-1">
        <!-- tabindex -1 keeps the popover's autofocus off the first row;
             the highlight bar is the only selection indicator -->
        <button
          v-for="(name, index) in TAG_COLOR_NAMES"
          :key="name"
          tabindex="-1"
          class="flex h-8 shrink-0 items-center gap-2 rounded px-2 text-base text-ink-gray-7"
          :class="{ 'bg-surface-alpha-gray-2': index === colorIndex }"
          @mouseenter="colorIndex = index"
          @click="pickColor(name)"
        >
          <span
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: TAG_COLORS[name] }"
          />
          {{ __(name) }}
        </button>
      </div>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { useTags, type Tag } from "@/composables/useTags";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { useEventListener } from "@vueuse/core";
import { Badge, MultiSelect, Popover, toast, Tooltip } from "frappe-ui";
import { computed, h, inject, nextTick, ref, watch } from "vue";
import { useRoute } from "vue-router";
import LucidePlus from "~icons/lucide/plus";
import ShortcutKey from "@/components/ShortcutKey.vue";
import TagChip from "./TagChip.vue";

// sentinel option value: picking it starts tag creation instead of a toggle
const CREATE_VALUE = "__create__";

// chips shown before collapsing into a "+N more" chip; collapse only past
// VISIBLE_TAGS + 1 so "+1 more" never replaces the one chip it hides
const VISIBLE_TAGS = 3;

// The HD Ticket Status palette (Gray first as the default pick); keys are
// stored on the Tag doc (Select field), values are frappe-ui's semantic
// surface tokens, which the theme overrides for dark mode (raw --red-500
// style vars carry light values only; Black inverts to near-white in dark
// so the dot keeps contrast)
const TAG_COLORS: Record<string, string> = {
  Gray: "var(--surface-gray-5)",
  Black: "var(--surface-gray-10)",
  Blue: "var(--surface-blue-6)",
  Green: "var(--surface-green-6)",
  Red: "var(--surface-red-6)",
  Pink: "var(--surface-pink-6)",
  Orange: "var(--surface-orange-6)",
  Amber: "var(--surface-amber-6)",
  Yellow: "var(--surface-yellow-6)",
  Cyan: "var(--surface-cyan-6)",
  Teal: "var(--surface-teal-6)",
  Violet: "var(--surface-violet-6)",
  Purple: "var(--surface-purple-6)",
};
const TAG_COLOR_NAMES = Object.keys(TAG_COLORS);

const ticket = inject(TicketSymbol)!;
const route = useRoute();
const { tagListResource, add, remove } = useTags(
  "HD Ticket",
  () => route.params.ticketId as string
);

const tagPickerOpen = ref(false);
const queryText = ref("");
const localTags = ref<string[]>([]);
// applied tags snapshot taken on open, so rows don't jump while toggling
const appliedAtOpen = ref<string[]>([]);
// true while a programmatic localTags write must not sync to the server
let muteSync = false;
// in-flight syncTags batches; the ticket reloads once the last one lands
let pendingSyncs = 0;

// color step state: pendingTag is the name awaiting a color pick
const colorPickerOpen = ref(false);
const pendingTag = ref("");
const colorIndex = ref(0);
// colour chosen for a not-yet-created tag, keyed by name; consumed by the
// sync so add_tag mints the master with it (add_tag colours on create only)
const pendingColors = ref<Record<string, string>>({});

const visibleTags = computed(() =>
  localTags.value.length > VISIBLE_TAGS + 1
    ? localTags.value.slice(0, VISIBLE_TAGS)
    : localTags.value
);
const hiddenTags = computed(() =>
  localTags.value.slice(visibleTags.value.length)
);
const headTags = computed(() => visibleTags.value.slice(0, -1));
const lastTag = computed(() => visibleTags.value.at(-1));

const appliedTags = computed<string[]>(() => [
  ...new Set(
    (ticket.value.doc?._user_tags || "")
      .split(",")
      .map((tag: string) => tag.trim())
      .filter(Boolean)
  ),
]);

const existingTagOptions = computed(() => {
  const applied = new Set(appliedAtOpen.value);
  const tags: { name: string; color?: string }[] = tagListResource.data || [];
  return [...tags]
    .sort(
      (a, b) =>
        Number(applied.has(b.name)) - Number(applied.has(a.name)) ||
        a.name.localeCompare(b.name)
    )
    .map((tag) => ({
      label: tag.name,
      value: tag.name,
      color: tag.color,
    }));
});

// The create row is a real option so keyboard navigation reaches it. Its
// label ends with the *raw* query (not the trimmed display text): the list
// matcher tests the query untrimmed, so a trailing space would otherwise
// filter the row out. The visible label below stays trimmed.
const tagOptions = computed(() => {
  const options: Record<string, unknown>[] = [...existingTagOptions.value];
  const text = queryText.value.trim();
  if (showCreateOption.value) {
    options.push({
      label: `${__("Create")} ${queryText.value}`,
      value: CREATE_VALUE,
      slots: {
        // full-row takeover skips the default row's checkbox; the classes
        // mirror ItemListRow's shell so the row sits like its siblings
        item: () =>
          h(
            "span",
            {
              class:
                "flex min-h-7 w-full min-w-0 items-center gap-2 px-2 py-1.5 text-base text-ink-gray-7",
            },
            [
              h(LucidePlus, { class: "size-3.5 shrink-0 text-ink-gray-5" }),
              h(
                "span",
                { class: "min-w-0 truncate" },
                `${__("Create")} "${text}"`
              ),
            ]
          ),
      },
    });
  }
  return options;
});

function colorToken(name?: string) {
  return TAG_COLORS[name ?? ""] ?? TAG_COLORS.Gray;
}

function tagColorToken(tag: string) {
  return colorToken(
    (tagListResource.data || []).find(
      (t: { name: string; color?: string }) => t.name === tag
    )?.color
  );
}

// the create row only appears while the query names a tag that doesn't exist
const showCreateOption = computed(() => {
  const text = queryText.value.trim().toLowerCase();
  if (!text) return false;
  return ![
    ...existingTagOptions.value.map((o) => o.value),
    ...localTags.value,
  ].some((name) => name.toLowerCase() === text);
});

const queryMatchesExistingTag = computed(() => {
  const text = queryText.value.trim().toLowerCase();
  return existingTagOptions.value.some((o) =>
    o.value.toLowerCase().includes(text)
  );
});

// Creating happens in two steps, like Linear: the name is validated here,
// then the tag picker swaps to the color popover; insertion waits for
// the color pick (Escape or outside click abandons cleanly)
function startCreate() {
  const tag = queryText.value.trim();
  if (colorPickerOpen.value || !tag || localTags.value.includes(tag)) return;
  // _user_tags is a comma-separated column; a comma would split the tag apart
  if (tag.includes(",")) {
    toast.error(__("Tag cannot contain commas"));
    return;
  }
  pendingTag.value = tag;
  tagPickerOpen.value = false;
  colorPickerOpen.value = true;
}

function pickColor(color: string) {
  const tag = pendingTag.value;
  colorPickerOpen.value = false;
  if (!tag || localTags.value.includes(tag)) return;
  pendingColors.value[tag] = color;
  // seed the list so the new chip's dot is coloured before the reload lands
  if (!(tagListResource.data || []).some((t: Tag) => t.name === tag)) {
    tagListResource.data = [
      ...(tagListResource.data || []),
      { name: tag, color },
    ];
  }
  // the localTags watcher syncs this as an add, passing the pending colour
  localTags.value = [...localTags.value, tag];
}

function handleColorKeydown(event: KeyboardEvent) {
  const count = TAG_COLOR_NAMES.length;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const step = event.key === "ArrowDown" ? 1 : -1;
    colorIndex.value = (colorIndex.value + step + count) % count;
  } else if (event.key === "Enter") {
    event.preventDefault();
    pickColor(TAG_COLOR_NAMES[colorIndex.value]);
  }
}

function syncTags(added: string[], removed: string[]) {
  const requests = [
    ...added.map((tag) => add(tag, pendingColors.value[tag])),
    ...removed.map((tag) => remove(tag)),
  ];
  added.forEach((tag) => delete pendingColors.value[tag]);
  if (!requests.length) return;
  pendingSyncs += 1;
  Promise.all(requests)
    .catch((error: any) =>
      toast.error(error?.messages?.join(", ") || __("Failed to update tags"))
    )
    .finally(() => {
      pendingSyncs -= 1;
      if (!pendingSyncs) ticket.value.reload();
    });
}

// While the picker is open (or syncs are in flight) localTags is the
// source of truth: writing server state into the model mid-open makes
// reka re-highlight the first checked row, teleporting the user's
// keyboard position; stale in-flight reloads would also briefly
// resurrect just-removed chips
function adoptServerTags() {
  if (tagPickerOpen.value || pendingSyncs) return;
  const tags = appliedTags.value;
  const local = localTags.value;
  if (tags.length === local.length && tags.every((t) => local.includes(t)))
    return;
  muteSync = true;
  localTags.value = [...tags];
  nextTick(() => (muteSync = false));
}

useShortcut("g", () => (tagPickerOpen.value = true));

// Document-level keys, capture phase (they must pre-empt reka's handlers
// on the search input): the color popover has no input to focus (Escape
// stays with reka's dismiss layer); Enter creates the tag when the create
// row is the only thing to act on -- with matching rows visible, Enter
// keeps reka's toggle-highlighted behavior
useEventListener(
  document,
  "keydown",
  (event: KeyboardEvent) => {
    if (colorPickerOpen.value) {
      handleColorKeydown(event);
      // The colour popover has no input to absorb keys, so single-key global
      // shortcuts (a, t, p, ...) would otherwise fire and close it. Swallow
      // everything here (capture pre-empts useShortcut's document listener);
      // Escape/Tab pass through for reka's dismiss and focus nav.
      if (event.key !== "Escape" && event.key !== "Tab") {
        event.stopPropagation();
      }
      return;
    }
    if (!tagPickerOpen.value || event.key !== "Enter") return;
    if (queryMatchesExistingTag.value || !showCreateOption.value) return;
    event.preventDefault();
    event.stopPropagation();
    startCreate();
  },
  { capture: true }
);

watch(appliedTags, adoptServerTags, { immediate: true });

watch(localTags, (next, previous) => {
  // selecting the create row lands here as a model change; divert it to
  // the color step instead of syncing it as a tag
  if (next.includes(CREATE_VALUE)) {
    localTags.value = next.filter((tag) => tag !== CREATE_VALUE);
    startCreate();
    return;
  }
  if (muteSync) return;
  syncTags(
    next.filter((tag) => !previous.includes(tag) && tag !== CREATE_VALUE),
    previous.filter((tag) => !next.includes(tag) && tag !== CREATE_VALUE)
  );
});

watch(tagPickerOpen, (open) => {
  queryText.value = "";
  if (open) {
    appliedAtOpen.value = [...localTags.value];
    tagListResource.reload();
  } else {
    // pick up any server-side changes that arrived while it was open
    adoptServerTags();
  }
});

watch(colorPickerOpen, (open) => {
  colorIndex.value = 0;
  if (!open) pendingTag.value = "";
});
</script>

<style>
/* Applied tags sit checked at the top of the list; the library's persistent
   gray fill on every checked row reads as a gray slab. Soften to the
   AssignTo/Linear look: plain rows, the checkbox carries the state. Scoped
   to this picker only via the marker rendered in the footer slot (the
   popover is portaled to body, so scoped styles can't reach it). */
[data-slot="content"][data-selection]:has(.ticket-tags-marker)
  [role="option"][data-state="checked"] {
  background: transparent;
}
[data-slot="content"][data-selection]:has(.ticket-tags-marker)
  [role="option"][data-highlighted] {
  background: var(--surface-alpha-gray-2);
}
/* Fixed width (13rem = w-52) so the popover doesn't track the chips row;
   long tag names truncate in their rows instead of widening it */
[data-slot="content"][data-selection]:has(.ticket-tags-marker) {
  width: 13rem;
}
[data-slot="content"][data-selection]:has(.ticket-tags-marker)
  [data-slot="item-label"] {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* In dark mode outline-gray-1 collapses onto the elevation-2 surface, so the
   search divider vanishes. Bump it to the next token to keep the separator. */
[data-slot="content"][data-selection]:has(.ticket-tags-marker)
  [data-slot="search"] {
  @apply border-outline-gray-2;
}
</style>

<style scoped>
/* Same curve as the selection-family popover motion (popoverMotion.css).
   Enter only: a chip swapping between the head list and the tail group
   must not play a leave animation, or it would briefly render twice. */
.tag-chip-enter-active {
  transition: opacity 180ms cubic-bezier(0.23, 1, 0.32, 1),
    transform 180ms cubic-bezier(0.23, 1, 0.32, 1);
}
.tag-chip-enter-from {
  opacity: 0;
  transform: scale(0.96);
}
/* the chip's own transition-colors makes Vue hold the leaving element for
   its duration; hide it at once so old and new tail never show together */
.tag-chip-leave-active {
  display: none;
}

@media (prefers-reduced-motion: reduce) {
  .tag-chip-enter-active {
    transition-duration: 0ms;
  }
}
</style>
