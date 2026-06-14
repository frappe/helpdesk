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
      <div
        class="my-2 w-80 rounded-lg border border-outline-gray-1 bg-surface-white shadow-xl"
      >
        <div class="relative overflow-clip rounded-[inherit]">
          <Transition
            :name="direction === 'forward' ? 'slide-forward' : 'slide-back'"
          >
            <div :key="step">
              <!-- Step: overview — the list of active filters -->
              <template v-if="step === 'overview'">
                <div
                  class="flex items-center border-b border-outline-gray-1 p-2 ps-3 h-9"
                >
                  <span class="text-base font-medium text-ink-gray-8">
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
                      <div class="gap-1">
                        <Button
                          variant="ghost"
                          icon="lucide-repeat"
                          class="invisible shrink-0 group-hover:visible"
                          :tooltip="__('Replace filter')"
                          @click="replaceFilter(filter)"
                        />
                        <Button
                          variant="ghost"
                          icon="lucide-x"
                          class="invisible shrink-0 group-hover:visible"
                          :tooltip="__('Remove filter')"
                          @click="removeFilter(filter.index)"
                        />
                      </div>
                    </div>
                  </div>
                  <div
                    class="mt-1 flex items-center justify-between border-t border-outline-gray-1 px-1 py-1.5"
                  >
                    <Button
                      variant="ghost"
                      :size="'xs'"
                      class="!text-ink-gray-5"
                      :label="__('Add filter')"
                      @click="step = 'fields'"
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
                  class="flex h-9 items-center border-b border-outline-gray-1"
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
import { computed, ref, watch } from "vue";
import {
  ActiveFilter,
  fieldIcon,
  FilterField,
  filterSummary,
  useFilterCore,
} from "./filterCore";
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
} = useFilterCore();

const step = ref<"overview" | "fields" | "value">("fields");
const selectedField = ref<FilterField | null>(null);
const editingIndex = ref<number | null>(null);
const editSession = ref(0);
// Where the value editor was opened from, so "back" returns there: the field
// list (when adding a new filter) or the overview (when editing an existing one).
const valueEditorOrigin = ref<"overview" | "fields">("overview");
let openPopoverFn: (() => void) | null = null;

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

function resetSteps() {
  step.value = activeFilters.value.length ? "overview" : "fields";
  selectedField.value = null;
  editingIndex.value = null;
}

function selectField(field: FilterField) {
  selectedField.value = field;
  editingIndex.value = null;
  valueEditorOrigin.value = "fields";
  editSession.value++;
  step.value = "value";
}

// "Replace" drops the existing condition and jumps to the field list so a
// different field can be picked in its place.
function replaceFilter(filter: ActiveFilter) {
  removeFilter(filter.index);
  step.value = "fields";
}

function editFilter(filter: ActiveFilter) {
  selectedField.value = filter.field;
  editingIndex.value = filter.index;
  valueEditorOrigin.value = "overview";
  editSession.value++;
  step.value = "value";
}

function applyFilter(operator: string, value: any) {
  if (!selectedField.value) return;
  if (editingIndex.value === null) {
    editingIndex.value = addFilter(selectedField.value, operator, value);
  } else {
    updateFilter(editingIndex.value, selectedField.value, operator, value);
  }
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
    step.value = "fields";
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
  background-color: var(--surface-white);
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
