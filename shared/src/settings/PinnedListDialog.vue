<template>
  <Dialog :open="show" size="md" bare @update:open="onOpenChange">
    <div class="flex flex-col" style="height: min(640px, calc(100vh - 8rem))">
      <div class="flex shrink-0 items-center justify-between px-4 pt-3">
        <div class="flex items-center gap-2">
          <Dialog.Title as-child>
            <h2 class="text-lg-medium text-ink-gray-9">
              {{ text.title }}
            </h2>
          </Dialog.Title>
          <!-- As the settings title shows it. -->
          <Badge
            v-if="hasUnsavedChanges"
            variant="subtle"
            theme="amber"
            size="sm"
            :label="__('Unsaved')"
          />
        </div>
        <Dialog.Close as-child>
          <Button variant="ghost" :label="__('Close')" icon="lucide-x" />
        </Dialog.Close>
      </div>

      <!-- The divider sits under the search, so scrolled rows clip against it -->
      <div class="shrink-0 border-b border-outline-gray-1 px-4 py-3">
        <TextInput
          v-model="query"
          :placeholder="text.search"
          :aria-label="text.search"
        >
          <template #prefix>
            <span
              class="lucide-search size-4 text-ink-gray-5"
              aria-hidden="true"
            />
          </template>
          <template v-if="query" #suffix>
            <Button
              variant="ghost"
              size="xs"
              icon="lucide-x"
              :label="__('Clear search')"
              @click="query = ''"
            />
          </template>
        </TextInput>
      </div>

      <ScrollArea class="min-h-0 flex-1" viewport-class="px-4 py-3">
        <div v-if="items.length" class="space-y-4">
          <section class="space-y-1.5">
            <h3 class="text-base-medium text-ink-gray-8">
              {{ __("Pinned") }}
            </h3>
            <!-- Search leaves the pins alone: it finds items to pin. -->
            <Draggable
              :list="pinnedItems"
              item-key="value"
              :group="GROUP"
              v-bind="DRAG_OPTIONS"
              :class="LIST"
              @change="onPinnedChange"
            >
              <template #item="{ element: item }">
                <div :class="[ROW, 'cursor-grab']">
                  <span
                    class="lucide-grip-vertical size-4 shrink-0 text-ink-gray-4"
                    aria-hidden="true"
                  />
                  <span
                    :class="item.icon"
                    class="size-4 shrink-0 text-ink-gray-6"
                  />
                  <span class="min-w-0 flex-1 truncate text-base">
                    {{ item.label }}
                  </span>
                  <CategoryAccessBadge :access="item.access" />
                  <Button
                    variant="ghost"
                    size="xs"
                    icon="lucide-pin-off"
                    :label="__('Unpin {0}', [item.label])"
                    :tooltip="__('Unpin')"
                    :class="ACTION"
                    @click.stop="moveTo(item.value, 'unpinned')"
                  />
                </div>
              </template>
              <template #footer>
                <div
                  v-if="!pinnedItems.length"
                  class="px-3 py-6 text-center text-p-sm text-ink-gray-5"
                >
                  {{ text.empty }}
                </div>
              </template>
            </Draggable>
          </section>

          <section class="space-y-1.5">
            <h3 class="text-base-medium text-ink-gray-8">
              {{ text.others }}
            </h3>
            <!-- Sorted A–Z, so a dropped row snaps into place. -->
            <Draggable
              :list="shownUnpinned"
              item-key="value"
              :group="GROUP"
              :disabled="Boolean(search)"
              :sort="false"
              v-bind="DRAG_OPTIONS"
              :class="LIST"
              @change="onUnpinnedChange"
            >
              <template #item="{ element: item }">
                <div :class="[ROW, search ? 'cursor-default' : 'cursor-grab']">
                  <span
                    v-if="!search"
                    class="lucide-grip-vertical size-4 shrink-0 text-ink-gray-4"
                    aria-hidden="true"
                  />
                  <span
                    :class="item.icon"
                    class="size-4 shrink-0 text-ink-gray-6"
                  />
                  <span class="min-w-0 flex-1 truncate text-base">
                    {{ item.label }}
                  </span>
                  <CategoryAccessBadge :access="item.access" />
                  <Button
                    variant="ghost"
                    size="xs"
                    icon="lucide-pin"
                    :label="__('Pin {0}', [item.label])"
                    :tooltip="__('Pin')"
                    :class="ACTION"
                    @click.stop="moveTo(item.value, 'pinned')"
                  />
                </div>
              </template>
              <template #footer>
                <div
                  v-if="!shownUnpinned.length"
                  class="px-3 py-6 text-center text-p-sm text-ink-gray-5"
                >
                  {{ search ? __("No matches") : text.allPinned }}
                </div>
                <div
                  v-else-if="hiddenCount"
                  class="px-3 py-2 text-center text-p-sm text-ink-gray-5"
                >
                  {{ __("Search to find {0} more", [hiddenCount]) }}
                </div>
              </template>
            </Draggable>
          </section>
        </div>

        <div v-else class="px-3 py-6 text-center text-p-sm text-ink-gray-5">
          {{ text.none }}
        </div>
      </ScrollArea>

      <div
        class="flex shrink-0 justify-between border-t border-outline-gray-1 px-4 py-3"
      >
        <Button
          variant="ghost"
          :label="__('Reset changes')"
          :disabled="!hasUnsavedChanges || isSaving"
          @click="selected = [...initial]"
        />
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="!hasUnsavedChanges"
          :loading="isSaving"
          @click="saveChanges"
        />
      </div>
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { askConfirm } from "../utils";
import { Badge, Button, Dialog, ScrollArea, TextInput } from "frappe-ui";
import { computed, ref, watch } from "vue";
import Draggable from "vuedraggable";
import CategoryAccessBadge from "./CategoryAccessBadge.vue";
import type { PinKind } from "./knowledgeBaseDraft";
import { pinnedListText } from "./pinnedListText";

type Section = "pinned" | "unpinned";
type Item = {
  label: string;
  value: string;
  icon: string;
  // Of its articles; "Mixed" when they differ.
  access?: string;
};
type Change = {
  added?: { element: Item; newIndex: number };
  moved?: { element: Item; newIndex: number };
};

const ROW =
  "group flex min-h-8 w-full select-none items-center gap-2 rounded-4 px-1.5 py-0.5 text-left text-ink-gray-8 hover:bg-surface-gray-2";
const ACTION = "shrink-0 text-ink-gray-5";
// No min height: the empty message is the drop target.
const LIST = "rounded-6 border border-outline-gray-2 px-1.5 py-2";
// Touch drags need a short hold, so the list still scrolls.
const GROUP = "pinned-items";
// A big knowledge base lists past this only through search.
const SHOWN_LIMIT = 100;
const DRAG_OPTIONS = {
  animation: 150,
  delay: 200,
  delayOnTouchOnly: true,
  ghostClass: "opacity-40",
};

const props = defineProps<{
  kind: PinKind;
  items: Item[];
  pinned: string[];
  // Resolves true on success.
  save: (pinned: string[]) => Promise<boolean>;
}>();

const show = defineModel<boolean>("open", { required: true });

const text = computed(() => pinnedListText(props.kind));
const query = ref("");
const search = computed(() => query.value.trim().toLowerCase());
const selected = ref<string[]>([]);
const initial = ref<string[]>([]);
const isSaving = ref(false);

// Reset on open, so closing without Save drops edits.
watch(show, (open) => {
  if (!open) return;
  query.value = "";
  selected.value = [...props.pinned];
  initial.value = [...props.pinned];
});

const byName = computed(
  () => new Map(props.items.map((item) => [item.value, item]))
);

const pinnedItems = computed(() =>
  selected.value
    .map((name) => byName.value.get(name))
    .filter((item): item is Item => item !== undefined)
);

// In the order the items come: A–Z.
const unpinnedItems = computed(() =>
  props.items.filter((item) => !selected.value.includes(item.value))
);

function matches(item: Item) {
  return item.label.toLowerCase().includes(search.value);
}

const matchingUnpinned = computed(() =>
  search.value ? unpinnedItems.value.filter(matches) : unpinnedItems.value
);
const shownUnpinned = computed(() =>
  matchingUnpinned.value.slice(0, SHOWN_LIMIT)
);
const hiddenCount = computed(
  () => matchingUnpinned.value.length - shownUnpinned.value.length
);

const hasUnsavedChanges = computed(
  () => selected.value.join() !== initial.value.join()
);

function onPinnedChange({ added, moved }: Change) {
  const change = added || moved;
  if (!change) return;
  // newIndex counts shown rows; pins to missing items aren't shown
  const names = pinnedItems.value
    .map((item) => item.value)
    .filter((name) => name !== change.element.value);
  names.splice(change.newIndex, 0, change.element.value);
  const missing = selected.value.filter((name) => !byName.value.has(name));
  selected.value = [...names, ...missing];
}

function onUnpinnedChange({ added }: Change) {
  if (added) moveTo(added.element.value, "unpinned");
}

function moveTo(name: string, section: Section) {
  const rest = selected.value.filter((row) => row !== name);
  selected.value = section === "pinned" ? [...rest, name] : rest;
}

// Closing with edits asks first.
function onOpenChange(open: boolean) {
  if (open || !hasUnsavedChanges.value) {
    show.value = open;
    return;
  }
  askConfirm({
    title: __("Unsaved changes"),
    message: __(
      "Are you sure you want to close? Unsaved changes will be lost."
    ),
    label: __("Confirm"),
    action: () => {
      show.value = false;
    },
  });
}

async function saveChanges() {
  if (isSaving.value || !hasUnsavedChanges.value) return;
  isSaving.value = true;
  try {
    if (await props.save(selected.value)) show.value = false;
  } finally {
    isSaving.value = false;
  }
}
</script>
