<template>
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
      <!-- explicit duration = timer-based cleanup, so a throttled background
           tab can't leave a removed chip stuck mid-transition -->
      <TransitionGroup
        tag="div"
        name="tag-chip"
        :duration="{ enter: 180, leave: 140 }"
        class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5"
      >
        <Badge
          v-for="tag in localTags"
          :key="tag"
          theme="gray"
          variant="outline"
          size="lg"
          class="max-w-40 transition-colors duration-150 hover:bg-surface-gray-2"
        >
          <span :title="tag" class="min-w-0 truncate">{{ tag }}</span>
        </Badge>
        <Tooltip key="add-tags" :text="`${__('Add labels')} (L)`">
          <!-- h-6 matches Badge size=lg so the row height never changes
               when the first chip appears (no layout shift) -->
          <button
            v-if="!localTags.length"
            class="inline-flex h-6 items-center rounded border border-dashed border-outline-gray-2 px-2 text-sm text-ink-gray-5 transition-[color,border-color,transform] duration-150 hover:border-outline-gray-3 hover:text-ink-gray-7 active:scale-[0.96]"
          >
            + {{ __("Add") }}
          </button>
          <!-- with tags present, collapse to a ghost + icon -->
          <button
            v-else
            class="inline-flex h-6 w-6 items-center justify-center rounded text-ink-gray-5 transition-[color,background-color,transform] duration-150 hover:bg-surface-gray-2 hover:text-ink-gray-7 active:scale-[0.96]"
          >
            <LucidePlus class="size-3.5" />
          </button>
        </Tooltip>
      </TransitionGroup>
    </template>
    <!-- No matches: the create row replaces the empty text, like Linear -->
    <template #empty="{ query }">
      <button
        v-if="query.trim()"
        :disabled="creating"
        class="text-p-sm -mx-2 -my-1.5 flex h-8 w-[calc(100%+16px)] items-center gap-2 rounded px-2 text-ink-gray-6 hover:bg-surface-gray-3 disabled:opacity-50"
        @click="createTag(query)"
      >
        <LucidePlus class="size-3.5 shrink-0" />
        <span class="min-w-0 truncate">
          {{ __("Create") }}
          <span class="text-ink-gray-5">"{{ query.trim() }}"</span>
        </span>
      </button>
      <span v-else class="text-p-sm">
        {{ __("No labels yet, type to create one") }}
      </span>
    </template>
    <!-- Partial matches but no exact one: create row pinned below results.
         The hidden marker scopes this picker's style overrides (see <style>) -->
    <template #footer="{ query }">
      <span class="ticket-tags-marker hidden" aria-hidden="true" />
      <button
        v-if="hasMatches(query) && showCreate(query)"
        :disabled="creating"
        class="text-p-sm flex h-8 w-full items-center gap-2 border-t border-outline-gray-1 px-3 text-ink-gray-6 hover:bg-surface-gray-3 disabled:opacity-50"
        @click="createTag(query)"
      >
        <LucidePlus class="size-3.5 shrink-0" />
        <span class="min-w-0 truncate">
          {{ __("Create") }}
          <span class="text-ink-gray-5">"{{ query.trim() }}"</span>
        </span>
      </button>
    </template>
  </MultiSelect>
</template>

<script setup lang="ts">
import { useShortcut } from "@/composables/shortcuts";
import { __ } from "@/translation";
import { TicketSymbol } from "@/types";
import { useEventListener } from "@vueuse/core";
import {
  Badge,
  call,
  createListResource,
  createResource,
  MultiSelect,
  toast,
  Tooltip,
} from "frappe-ui";
import { computed, inject, nextTick, ref, watch } from "vue";
import LucidePlus from "~icons/lucide/plus";

const ticket = inject(TicketSymbol)!;

const pickerOpen = ref(false);
const creating = ref(false);
const queryText = ref("");
const localTags = ref<string[]>([]);
// applied tags snapshot taken on open, so rows don't jump while toggling
const appliedAtOpen = ref<string[]>([]);
let syncingFromServer = false;

const tagsResource = createListResource({
  doctype: "Tag",
  fields: ["name"],
  cache: ["Tags", "Helpdesk"],
  filters: { app: "helpdesk" },
  orderBy: "name asc",
  pageLength: 500,
});

const addTagResource = createResource({
  url: "frappe.desk.doctype.tag.tag.add_tag",
});
const removeTagResource = createResource({
  url: "frappe.desk.doctype.tag.tag.remove_tag",
});

const appliedTags = computed<string[]>(() => [
  ...new Set(
    (ticket.value.doc?._user_tags || "")
      .split(",")
      .map((tag: string) => tag.trim())
      .filter(Boolean)
  ),
]);

const tagOptions = computed(() => {
  const applied = new Set(appliedAtOpen.value);
  const names: string[] = (tagsResource.data || []).map(
    (tag: { name: string }) => tag.name
  );
  return names
    .sort(
      (a, b) =>
        Number(applied.has(b)) - Number(applied.has(a)) || a.localeCompare(b)
    )
    .map((name) => ({ label: name, value: name }));
});

function showCreate(query: string) {
  const text = query.trim().toLowerCase();
  if (!text) return false;
  return ![...tagOptions.value.map((o) => o.value), ...localTags.value].some(
    (name) => name.toLowerCase() === text
  );
}

function hasMatches(query: string) {
  const text = query.trim().toLowerCase();
  return tagOptions.value.some((o) => o.value.toLowerCase().includes(text));
}

async function createTag(query: string) {
  const tag = query.trim();
  if (creating.value || localTags.value.includes(tag)) return;
  // _user_tags is a comma-separated column; a comma would split the tag apart
  if (tag.includes(",")) {
    toast.error(__("Label cannot contain commas"));
    return;
  }
  creating.value = true;
  try {
    await call("frappe.client.insert", {
      doc: { doctype: "Tag", name: tag, app: "helpdesk" },
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
  if (!localTags.value.includes(tag)) {
    localTags.value = [...localTags.value, tag];
  }
  tagsResource.reload();
  clearQuery();
}

// MultiSelect only resets its search on close; clear its input directly so
// the list unfilters right after a create (scoped via our footer marker)
function clearQuery() {
  const input = document.querySelector<HTMLInputElement>(
    "[data-slot='content'][data-selection]:has(.ticket-tags-marker) [data-slot='input']"
  );
  if (!input) return;
  const setter = Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    "value"
  )?.set;
  setter?.call(input, "");
  input.dispatchEvent(new Event("input", { bubbles: true }));
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

// Enter creates the tag when the create row is the only thing to act on;
// with matching rows visible, Enter keeps reka's toggle-highlighted behavior
useEventListener(document, "keydown", (event: KeyboardEvent) => {
  if (!pickerOpen.value || event.key !== "Enter") return;
  if (hasMatches(queryText.value) || !showCreate(queryText.value)) return;
  event.preventDefault();
  event.stopPropagation();
  createTag(queryText.value);
});

watch(
  appliedTags,
  (tags) => {
    syncingFromServer = true;
    localTags.value = [...tags];
    nextTick(() => (syncingFromServer = false));
  },
  { immediate: true }
);

watch(localTags, (next, previous) => {
  if (syncingFromServer) return;
  syncTags(
    next.filter((tag) => !previous.includes(tag)),
    previous.filter((tag) => !next.includes(tag))
  );
});

watch(pickerOpen, (open) => {
  queryText.value = "";
  if (!open) return;
  appliedAtOpen.value = [...localTags.value];
  tagsResource.reload();
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
/* Same curve and rhythm as the selection-family popover motion
   (popoverMotion.css): 180ms enter, softer 140ms exit. */
.tag-chip-enter-active {
  transition: opacity 180ms cubic-bezier(0.23, 1, 0.32, 1),
    transform 180ms cubic-bezier(0.23, 1, 0.32, 1);
}
.tag-chip-leave-active {
  position: absolute;
  transition: opacity 140ms cubic-bezier(0.23, 1, 0.32, 1),
    transform 140ms cubic-bezier(0.23, 1, 0.32, 1);
}
.tag-chip-enter-from {
  opacity: 0;
  transform: scale(0.96);
}
.tag-chip-leave-to {
  opacity: 0;
  transform: scale(0.985);
}
.tag-chip-move {
  transition: transform 180ms cubic-bezier(0.23, 1, 0.32, 1);
}

@media (prefers-reduced-motion: reduce) {
  .tag-chip-enter-active,
  .tag-chip-leave-active,
  .tag-chip-move {
    transition-duration: 0ms;
  }
}
</style>
