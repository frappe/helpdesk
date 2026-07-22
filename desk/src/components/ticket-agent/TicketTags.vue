<template>
  <!-- The color step is a sibling popover on the same anchor, so it opens
       exactly where the label picker just closed, reading as an in-place
       content swap (Linear's create-label flow) -->
  <Popover v-model:open="colorPickerOpen" side="left" align="start">
    <!-- plain div anchor: MultiSelect's own root is display:contents,
         which would give the PopoverAnchor a zero rect -->
    <template #target>
      <div>
        <MultiSelect
          v-model="localTags"
          v-model:open="pickerOpen"
          :options="tagOptions"
          :loading="tagsResource.loading"
          :placeholder="__('Search or create labels')"
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
              <!-- the last chip and the button form one flex item, so the +
                   can never wrap onto a line of its own; new tags land at
                   the end of localTags, so the enter transition still plays
                   on every freshly added chip -->
              <div class="flex min-w-0 max-w-full items-center gap-1.5">
                <Transition name="tag-chip">
                  <TagChip
                    v-if="lastTag"
                    :key="lastTag"
                    :tag="lastTag"
                    :color="tagColorToken(lastTag)"
                  />
                </Transition>
                <Tooltip :text="`${__('Add labels')} (L)`">
                  <!-- h-6 matches Badge size=lg so the row height never changes
                 when the first chip appears (no layout shift) -->
                  <button
                    v-if="!localTags.length"
                    class="inline-flex h-6 items-center rounded-full border border-dashed border-outline-gray-2 px-2 text-sm text-ink-gray-5 transition-[color,border-color,transform] duration-150 hover:border-outline-gray-3 hover:text-ink-gray-7 active:scale-[0.96]"
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
            </div>
          </template>
          <template #item-prefix="{ item }">
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: colorToken(item.color) }"
            />
          </template>
          <template #empty>
            <span class="text-p-sm">
              {{ __("No labels yet, type to create one") }}
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
      <!-- live preview of the label being created: the dot tracks the
           highlighted color -->
      <p
        class="flex items-center gap-2 border-b border-outline-gray-1 px-3 py-2 text-base text-ink-gray-8"
      >
        <span
          class="size-2.5 shrink-0 rounded-full"
          :style="{ backgroundColor: LABEL_COLORS[colorIndex].token }"
        />
        <span class="min-w-0 truncate">{{ pendingTag }}</span>
      </p>
      <div class="flex flex-col p-1">
        <!-- tabindex -1 keeps the popover's autofocus off the first row;
             the highlight bar is the only selection indicator -->
        <button
          v-for="(color, index) in LABEL_COLORS"
          :key="color.name"
          tabindex="-1"
          class="flex h-8 shrink-0 items-center gap-2 rounded px-2 text-base text-ink-gray-7"
          :class="{ 'bg-surface-alpha-gray-2': index === colorIndex }"
          @mouseenter="colorIndex = index"
          @click="pickColor(color)"
        >
          <span
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: color.token }"
          />
          {{ __(color.name) }}
        </button>
      </div>
    </div>
  </Popover>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { useEventListener } from "@vueuse/core";
import {
  call,
  createListResource,
  createResource,
  MultiSelect,
  Popover,
  toast,
  Tooltip,
} from "frappe-ui";
import { computed, h, inject, nextTick, ref, watch } from "vue";
import LucidePlus from "~icons/lucide/plus";
import TagChip from "./TagChip.vue";

// sentinel option value: picking it starts label creation instead of a toggle
const CREATE_VALUE = "__create__";

// The HD Ticket Status palette (Gray first as the default pick); names are
// stored on the Tag doc (Select field), dots use the matching frappe-ui
// -500 tokens (theme-aware, so they flip correctly in dark mode)
const LABEL_COLORS = [
  { name: "Gray", token: "var(--gray-400)" },
  { name: "Black", token: "var(--gray-900)" },
  { name: "Blue", token: "var(--blue-500)" },
  { name: "Green", token: "var(--green-500)" },
  { name: "Red", token: "var(--red-500)" },
  { name: "Pink", token: "var(--pink-500)" },
  { name: "Orange", token: "var(--orange-500)" },
  { name: "Amber", token: "var(--amber-500)" },
  { name: "Yellow", token: "var(--yellow-500)" },
  { name: "Cyan", token: "var(--cyan-500)" },
  { name: "Teal", token: "var(--teal-500)" },
  { name: "Violet", token: "var(--violet-500)" },
  { name: "Purple", token: "var(--purple-500)" },
];

const ticket = inject(TicketSymbol)!;

const pickerOpen = ref(false);
const creating = ref(false);
const queryText = ref("");
const localTags = ref<string[]>([]);
// applied tags snapshot taken on open, so rows don't jump while toggling
const appliedAtOpen = ref<string[]>([]);
let syncingFromServer = false;

// color step state: pendingTag is the name awaiting a color pick
const colorPickerOpen = ref(false);
const pendingTag = ref("");
const colorIndex = ref(0);

const tagsResource = createListResource({
  doctype: "Tag",
  fields: ["name", "color"],
  cache: ["Tags", "Helpdesk"],
  filters: { app: "helpdesk" },
  orderBy: "name asc",
  pageLength: 500,
  auto: true,
});

const addTagResource = createResource({
  url: "frappe.desk.doctype.tag.tag.add_tag",
});
const removeTagResource = createResource({
  url: "frappe.desk.doctype.tag.tag.remove_tag",
});

const headTags = computed(() => localTags.value.slice(0, -1));
const lastTag = computed(() => localTags.value.at(-1));

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
  const tags: { name: string; color?: string }[] = tagsResource.data || [];
  return [...tags]
    .sort(
      (a, b) =>
        Number(applied.has(b.name)) - Number(applied.has(a.name)) ||
        a.name.localeCompare(b.name)
    )
    .map((tag) => ({ label: tag.name, value: tag.name, color: tag.color }));
});

// The create row is a real option so keyboard navigation reaches it; its
// label contains the query, which keeps it visible under reka's filter
const tagOptions = computed(() => {
  const options: Record<string, unknown>[] = [...existingTagOptions.value];
  const text = queryText.value.trim();
  if (showCreateOption.value) {
    options.push({
      label: `${__("Create")} "${text}"`,
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
  return (LABEL_COLORS.find((c) => c.name === name) ?? LABEL_COLORS[0]).token;
}

function tagColorToken(tag: string) {
  return colorToken(
    (tagsResource.data || []).find(
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
// then the label picker swaps to the color popover; insertion waits for
// the color pick (Escape or outside click abandons cleanly)
function startCreate() {
  const tag = queryText.value.trim();
  if (colorPickerOpen.value || !tag || localTags.value.includes(tag)) return;
  // _user_tags is a comma-separated column; a comma would split the tag apart
  if (tag.includes(",")) {
    toast.error(__("Label cannot contain commas"));
    return;
  }
  pendingTag.value = tag;
  pickerOpen.value = false;
  colorPickerOpen.value = true;
}

async function pickColor(color: { name: string }) {
  const tag = pendingTag.value;
  if (creating.value || !tag) return;
  creating.value = true;
  try {
    await call("frappe.client.insert", {
      doc: { doctype: "Tag", name: tag, app: "helpdesk", color: color.name },
    });
  } catch (error: any) {
    // duplicate = a tag outside helpdesk with this name; just apply it
    if (!error?.exc_type?.includes("DuplicateEntryError")) {
      toast.error(error.messages?.join(", ") || __("Failed to create label"));
      return;
    }
  } finally {
    creating.value = false;
  }
  colorPickerOpen.value = false;
  if (!localTags.value.includes(tag)) {
    localTags.value = [...localTags.value, tag];
  }
  // seed the list so the new chip's dot is colored before the reload lands
  tagsResource.data = [
    ...(tagsResource.data || []),
    { name: tag, color: color.name },
  ];
  tagsResource.reload();
}

function handleColorKeydown(event: KeyboardEvent) {
  const count = LABEL_COLORS.length;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    const step = event.key === "ArrowDown" ? 1 : -1;
    colorIndex.value = (colorIndex.value + step + count) % count;
  } else if (event.key === "Enter") {
    event.preventDefault();
    pickColor(LABEL_COLORS[colorIndex.value]);
  }
}

function syncTags(added: string[], removed: string[]) {
  const params = (tag: string) => ({
    tag,
    dt: "HD Ticket",
    dn: ticket.value.doc.name,
  });
  const requests = [
    ...added.map((tag) => addTagResource.submit(params(tag))),
    ...removed.map((tag) => removeTagResource.submit(params(tag))),
  ];
  if (!requests.length) return;
  Promise.all(requests)
    .catch((error: any) =>
      toast.error(error?.messages?.join(", ") || __("Failed to update labels"))
    )
    .finally(() => ticket.value.reload());
}

useShortcut("l", () => (pickerOpen.value = true));

// Document-level keys: the color popover has no input to focus (Escape stays
// with reka's dismiss layer), and in the label picker Enter creates the tag
// when the create row is the only thing to act on -- with matching rows
// visible, Enter keeps reka's toggle-highlighted behavior
useEventListener(document, "keydown", (event: KeyboardEvent) => {
  if (colorPickerOpen.value) return handleColorKeydown(event);
  if (!pickerOpen.value || event.key !== "Enter") return;
  if (queryMatchesExistingTag.value || !showCreateOption.value) return;
  event.preventDefault();
  event.stopPropagation();
  startCreate();
});

watch(
  appliedTags,
  (tags) => {
    // replacing localTags with an equal-but-new array round-trips into
    // reka, whose model watcher re-highlights the first checked row --
    // the picker's highlight would jump to the top after every save
    const local = localTags.value;
    if (tags.length === local.length && tags.every((t) => local.includes(t)))
      return;
    syncingFromServer = true;
    localTags.value = [...tags];
    nextTick(() => (syncingFromServer = false));
  },
  { immediate: true }
);

watch(localTags, (next, previous) => {
  // selecting the create row lands here as a model change; divert it to
  // the color step instead of syncing it as a tag
  if (next.includes(CREATE_VALUE)) {
    localTags.value = next.filter((tag) => tag !== CREATE_VALUE);
    startCreate();
    return;
  }
  if (syncingFromServer) return;
  syncTags(
    next.filter((tag) => !previous.includes(tag) && tag !== CREATE_VALUE),
    previous.filter((tag) => !next.includes(tag) && tag !== CREATE_VALUE)
  );
});

watch(pickerOpen, (open) => {
  queryText.value = "";
  if (!open) return;
  appliedAtOpen.value = [...localTags.value];
  tagsResource.reload();
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
