<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover, open }">
      <div :ref="() => (openPopoverFn = open)" class="w-fit">
        <FilterTrigger
          :count="activeFilters.length"
          @toggle="openPopover(togglePopover)"
          @clear="clearFilters()"
        />
      </div>
    </template>
    <template #body>
      <!-- Dedicated high-z layer the operator dropdown teleports into. Both this
           and the frappe-ui Popover panel land in <body>; the popover panel is
           z-[100], so a body-mounted menu (z-auto) renders behind it. This layer
           establishes a z-[101] stacking context above the panel, and owning it
           here keeps the fix scoped to the filter. -->
      <Teleport to="body">
        <div ref="operatorMenuLayer" class="relative z-[101]" />
      </Teleport>
      <div
        class="my-2 w-80 rounded-lg border border-outline-gray-1 bg-surface-base shadow-xl"
      >
        <div class="relative overflow-clip rounded-[inherit]">
          <Transition
            :name="direction === 'forward' ? 'slide-forward' : 'slide-back'"
          >
            <div :key="step">
              <!-- Step: overview — the list of active filters -->
              <template v-if="step === 'overview'">
                <div
                  ref="overviewHeader"
                  tabindex="-1"
                  class="flex items-center border-b border-outline-gray-1 p-2 ps-3 h-9 outline-none"
                  @vue:mounted="focusOverview"
                >
                  <span class="text-base-medium text-ink-gray-8">
                    {{ headerLabel }}
                  </span>
                </div>
                <div>
                  <div class="p-1.5">
                    <div
                      v-for="filter in activeFilters"
                      :key="filter.index"
                      class="group flex h-8 w-full items-center gap-2 rounded px-1.5 hover:bg-surface-gray-2 pl-0"
                    >
                      <Button
                        variant="ghost"
                        :label="filterSummary(filter)"
                        :tooltip="filterSummary(filter)"
                        class="!h-full min-w-0 flex-1 !justify-start !px-0 hover:!bg-transparent !pl-1.5"
                        @click="editFilter(filter)"
                      >
                        <template #prefix>
                          <component
                            :is="fieldIcon(filter.field)"
                            class="size-4 shrink-0 text-ink-gray-5"
                          />
                        </template>
                      </Button>
                      <div class="flex shrink-0 items-center gap-1">
                        <Button
                          variant="ghost"
                          icon="lucide-arrow-left-right"
                          :aria-label="__('Replace filter')"
                          :tooltip="__('Replace filter')"
                          :class="revealOnRowActivity"
                          @click="replaceFilter(filter)"
                        />
                        <Button
                          variant="ghost"
                          icon="lucide-x"
                          :aria-label="__('Remove filter')"
                          :tooltip="__('Remove filter')"
                          :class="revealOnRowActivity"
                          @click="removeFilter(filter.index)"
                        />
                      </div>
                    </div>
                  </div>
                  <div
                    class="flex items-center justify-between border-t border-outline-gray-1 px-1 py-1.5"
                  >
                    <Button
                      variant="ghost"
                      :size="'xs'"
                      class="!text-ink-gray-5"
                      :label="__('Add filter')"
                      @click="addNewFilter()"
                      tooltip="Add Filter (A)"
                    >
                      <template #prefix>
                        <LucidePlus class="size-4" />
                      </template>
                    </Button>
                    <Button
                      :size="'xs'"
                      variant="ghost"
                      class="!text-ink-gray-5"
                      :label="__('Clear all')"
                      :icon-left="'lucide-trash-2'"
                      @click="clearFilters()"
                    />
                  </div>
                </div>
              </template>

              <!-- Step: fields — choose which field to filter on -->
              <template v-else-if="step === 'fields'">
                <div
                  v-if="canGoBack"
                  class="flex h-9 items-center border-b border-outline-gray-1 ps-1"
                >
                  <BackButton :label="headerLabel" size="sm" @back="goBack" />
                </div>
                <FilterFieldList
                  :fields="fields"
                  :placeholder="
                    canGoBack ? __('Search fields...') : __('Add Filter...')
                  "
                  :show-shortcut-hint="!activeFilters.length"
                  @select="selectField"
                  @back="goBack"
                />
              </template>

              <!-- Step: value — pick operator + value (renders its own header) -->
              <FilterValueEditor
                v-else-if="step === 'value' && selectedField"
                :key="editSession"
                :field="selectedField"
                :filter="editingFilter"
                :operator-menu-target="operatorMenuLayer"
                @apply="applyFilter"
                @clear="clearCurrentFilter"
                @back="goBack"
                @done="step = 'overview'"
              />
            </div>
          </Transition>
        </div>
      </div>
    </template>
  </Popover>
</template>

<script setup lang="ts">
import BackButton from "@/components/BackButton.vue";
import { useShortcut } from "@/composables/shortcuts";
import { __ } from "@/translation";
import { useEventListener } from "@vueuse/core";
import { Button, Popover } from "frappe-ui";
import { computed, nextTick, ref, watch } from "vue";
import {
  ActiveFilter,
  fieldIcon,
  FilterField,
  filterSummary,
  useFilter,
} from "./filter";
import FilterFieldList from "./FilterFieldList.vue";
import FilterTrigger from "./FilterTrigger.vue";
import FilterValueEditor from "./FilterValueEditor.vue";

const {
  fields,
  activeFilters,
  addFilter,
  updateFilter,
  removeFilter,
  clearFilters,
} = useFilter();

const step = ref<"overview" | "fields" | "value">("fields");
const selectedField = ref<FilterField | null>(null);
const editingIndex = ref<number | null>(null);
// The row a "Replace" is targeting. The old condition is kept untouched until a
// new one is chosen, so backing out leaves the original filter intact; the
// replacement then lands at this same position.
const replacingIndex = ref<number | null>(null);
const editSession = ref(0);
// Where the value editor was opened from, so "back" returns there: the field
// list (when adding a new filter) or the overview (when editing an existing one).
const valueEditorOrigin = ref<"overview" | "fields">("overview");
const overviewHeader = ref<HTMLElement | null>(null);
// The high-z layer the operator dropdown teleports into (see #body), so its menu
// sits above the filter popover panel instead of behind it.
const operatorMenuLayer = ref<HTMLElement | null>(null);
let openPopoverFn: (() => void) | null = null;

// Row actions stay out of the way until the row is hovered or focused.
const revealOnRowActivity =
  "opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 [@media(hover:none)]:opacity-100";

// used for animating back or forward between steps
const stepOrder = { overview: 0, fields: 1, value: 2 } as const;
const direction = ref<"forward" | "back">("forward");

const headerLabel = computed(() => {
  if (step.value === "overview") return __("Filters");
  if (step.value === "fields") return __("Choose a field");
  return selectedField.value?.label || "";
});

const canGoBack = computed(() => {
  if (step.value === "value") return true;
  return step.value === "fields" && activeFilters.value.length > 0;
});

const editingFilter = computed<ActiveFilter | null>(() => {
  if (editingIndex.value === null) return null;
  return (
    activeFilters.value.find((f) => f.index === editingIndex.value) || null
  );
});

useShortcut("f", () => {
  resetSteps();
  openPopoverFn?.();
});

function openPopover(toggle: () => void) {
  resetSteps();
  toggle();
}

// The popover auto-focuses its first focusable element on open, which would put
// a focus ring on the first filter row. Pull focus to the (non-tabbable) header
// instead so the overview opens without a row looking selected.
function focusOverview() {
  nextTick(() => overviewHeader.value?.focus({ preventScroll: true }));
}

function resetSteps() {
  step.value = activeFilters.value.length ? "overview" : "fields";
  selectedField.value = null;
  editingIndex.value = null;
  replacingIndex.value = null;
}

// Opens the field list to add a fresh filter, cancelling any pending replace.
function addNewFilter() {
  replacingIndex.value = null;
  step.value = "fields";
}

function selectField(field: FilterField) {
  selectedField.value = field;
  editingIndex.value = null;
  valueEditorOrigin.value = "fields";
  editSession.value++;
  step.value = "value";
}

// "Replace" jumps to the field list to pick a different field, but keeps the
// existing condition in place — it's only swapped out once the new one is
// applied (see applyFilter), so abandoning the flow loses nothing.
function replaceFilter(filter: ActiveFilter) {
  replacingIndex.value = filter.index;
  step.value = "fields";
}

function editFilter(filter: ActiveFilter) {
  selectedField.value = filter.field;
  editingIndex.value = filter.index;
  replacingIndex.value = null;
  valueEditorOrigin.value = "overview";
  editSession.value++;
  step.value = "value";
}

function applyFilter(operator: string, value: any) {
  if (!selectedField.value) return;
  // A pending replace overwrites its target row in place; otherwise we update
  // the row being edited, or append a brand-new filter.
  const targetIndex = replacingIndex.value ?? editingIndex.value;
  if (targetIndex === null) {
    editingIndex.value = addFilter(selectedField.value, operator, value);
  } else {
    updateFilter(targetIndex, selectedField.value, operator, value);
    editingIndex.value = targetIndex;
  }
  replacingIndex.value = null;
}

function clearCurrentFilter() {
  if (editingIndex.value === null) return;
  removeFilter(editingIndex.value);
  editingIndex.value = null;
}

// "Back" returns to wherever the current step was opened from: the value editor
// to its origin (field list or overview), and the field list to the overview.
function goBack() {
  if (step.value === "value") {
    step.value = valueEditorOrigin.value;
    return;
  }
  step.value = activeFilters.value.length ? "overview" : "fields";
}

watch(step, (to, from) => {
  direction.value = stepOrder[to] >= stepOrder[from] ? "forward" : "back";
});

watch(activeFilters, (filters) => {
  if (step.value === "overview" && !filters.length) step.value = "fields";
});

// On the overview step, "a" jumps to the add-filter (field) step.
useEventListener(document, "keydown", (event: KeyboardEvent) => {
  if (step.value !== "overview" || event.metaKey || event.ctrlKey) return;
  const el = document.activeElement;
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
    return;
  }
  if (event.key === "a" || event.key === "A") {
    event.preventDefault();
    addNewFilter();
  }
});
</script>

<style scoped>
/* Panels are transparent at rest so they never paint over the popover border;
   they only need their own background while two of them overlap mid-swipe. */
.slide-forward-enter-active,
.slide-forward-leave-active,
.slide-back-enter-active,
.slide-back-leave-active {
  background-color: var(--surface-base);
  transition: transform 250ms cubic-bezier(0.2, 0, 0, 1),
    opacity 250ms cubic-bezier(0.2, 0, 0, 1);
}

/* The outgoing panel leaves the flow so both panels can swipe at once; the
   incoming forward panel stacks above it, like a navigation push. */
.slide-forward-leave-active,
.slide-back-leave-active {
  position: absolute;
  top: 0;
  inset-inline: 0;
}

.slide-forward-enter-active {
  position: relative;
  z-index: 1;
}

.slide-forward-enter-from,
.slide-back-leave-to {
  transform: translateX(100%);
}

.slide-forward-leave-to,
.slide-back-enter-from {
  transform: translateX(-25%);
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .slide-forward-enter-active,
  .slide-forward-leave-active,
  .slide-back-enter-active,
  .slide-back-leave-active {
    transition-duration: 0s;
  }
}
</style>
