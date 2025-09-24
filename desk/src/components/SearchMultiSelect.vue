<template>
  <div class="relative inline-block text-left">
    <div class="flex">
      <Button
        variant="outline"
        :class="{ 'ring-2 ring-outline-gray-2': isOpen }"
        @click="toggleDropdown"
      >
        <div
          class="flex items-center min-h-[20px]"
          :class="{ 'gap-2': hasSelectedImages && selectedCount > 0 }"
        >
          <template v-if="selectedCount > 0">
            <!-- Stacked Avatars -->
            <div class="flex -space-x-2 isolate">
              <div
                v-for="(option, index) in selectedOptions.slice(0, 3)"
                :key="`avatar-${option.value}`"
                class="relative flex"
                :style="{ zIndex: 10 - index }"
              >
                <Avatar
                  v-if="option.image"
                  :image="option.image"
                  :label="option.label"
                  class="border-2 border-white flex-shrink-0"
                  size="sm"
                />
              </div>
            </div>
            <!-- Count Text -->
            <span class="text-ink-gray-7">
              {{
                selectedCount === 1
                  ? selectedOptions[0].label
                  : `${selectedCount} ${selectionText}`
              }}
            </span>
          </template>
          <span v-else class="text-ink-gray-6">{{ placeholder }}</span>
        </div>
        <template #suffix>
          <LucideChevronDown
            class="ml-2 h-4 w-4 transition-transform duration-200"
            :class="{ 'rotate-180': isOpen }"
          />
        </template>
      </Button>
    </div>

    <div
      v-if="isOpen"
      class="absolute z-50 mt-2 w-64 divide-y divide-outline-gray-modals rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none left-0 origin-top-left"
    >
      <!-- Header -->
      <div class="py-1.5 px-1.5">
        <div
          class="flex h-7 items-center text-sm font-medium text-ink-gray-6 justify-between"
        >
          <input
            ref="inputRef"
            v-model="filterText"
            :placeholder="label"
            class="px-2 flex-1 bg-transparent border-none outline-none text-sm focus:border-none focus:ring-0 text-ink-gray-6 placeholder-ink-gray-4"
            @click.stop
            @keydown="handleInputKeydown"
          />
          <Button
            variant="ghost"
            size="sm"
            v-if="selectedCount > 0"
            @click="clearAll"
          >
            <template #icon>
              <LucideX class="size-4" />
            </template>
          </Button>
        </div>
      </div>

      <!-- Options List -->
      <div class="px-1.5 pb-1.5 max-h-64 overflow-y-auto">
        <!-- Individual Options (ungrouped) -->
        <div class="pt-1.5" v-if="filteredIndividualOptions.length > 0">
          <button
            v-for="option in filteredIndividualOptions"
            :key="`individual-${option.value}`"
            class="group flex h-7 w-full items-center rounded px-2 text-base hover:bg-surface-gray-3 text-ink-gray-6"
            :class="{ 'bg-surface-gray-2': isHighlighted(option) }"
            @click="toggleOption(option)"
          >
            <Checkbox
              :modelValue="props.modelValue.includes(option.value)"
              class="mr-2 flex-shrink-0"
            />

            <component v-if="option.icon" :is="renderIcon(option.icon)" />

            <Avatar
              v-else-if="hasAnyVisualElements"
              :image="option.image"
              :label="option.label"
              class="mr-2 flex-shrink-0"
              size="sm"
            />

            <span class="text-ink-gray-7 flex-1 text-left truncate">
              {{ option.label }}
            </span>

            <span
              v-if="(option.count ?? 0) > 0"
              class="text-xs text-ink-gray-5 ml-auto"
            >
              {{ option.count }}
            </span>
          </button>
        </div>

        <!-- Grouped Options -->
        <div v-for="group in filteredGroups" :key="`group-${group.group}`">
          <!-- Group Header -->
          <div
            class="flex h-7 pt-1.5 sticky top-0 bg-surface-white items-center px-2 text-sm font-medium text-ink-gray-6"
          >
            {{ group.group }}
          </div>

          <!-- Group Options -->
          <button
            v-for="option in group.items"
            :key="`grouped-${option.value}`"
            class="group flex h-7 w-full items-center rounded px-2 text-base hover:bg-surface-gray-3 text-ink-gray-6"
            :class="{ 'bg-surface-gray-2': isHighlighted(option) }"
            @click="toggleOption(option)"
          >
            <Checkbox
              :modelValue="props.modelValue.includes(option.value)"
              class="mr-2 flex-shrink-0"
            />

            <component v-if="option.icon" :is="renderIcon(option.icon)" />

            <Avatar
              v-else-if="option.image"
              :image="option.image"
              :label="option.label"
              class="mr-2 flex-shrink-0"
              size="sm"
            />

            <!-- Spacer for alignment when other options have visual elements -->
            <div
              v-else-if="hasAnyVisualElements"
              class="mr-2 w-6 h-6 flex-shrink-0"
            ></div>

            <span class="text-ink-gray-7 flex-1 text-left truncate">
              {{ option.label }}
            </span>

            <span
              v-if="(option.count ?? 0) > 0"
              class="text-xs text-ink-gray-5 ml-auto"
            >
              {{ option.count }}
            </span>
          </button>
        </div>

        <!-- No options message -->
        <div
          v-if="filteredOptions.length === 0"
          class="px-2 py-4 text-center text-sm text-ink-gray-5"
        >
          No options found
        </div>
      </div>
    </div>

    <!-- Overlay to close dropdown -->
    <div v-if="isOpen" class="fixed inset-0 z-40" @click="closeDropdown"></div>
  </div>
</template>

<script setup lang="ts">
import { Avatar, Button, Checkbox } from "frappe-ui";
import {
  computed,
  h,
  nextTick,
  ref,
  useTemplateRef,
  watch,
  type Component,
} from "vue";
import LucideChevronDown from "~icons/lucide/chevron-down";
import LucideX from "~icons/lucide/x";

// Type Definitions
interface MultiSelectOption {
  value: string;
  label: string;
  count?: number;
  image?: string;
  icon?: string | Component;
}

interface MultiSelectGroup {
  group: string;
  items: MultiSelectOption[];
}

// Support both flat options and grouped options in the same prop
type MultiSelectData = MultiSelectOption[] | MultiSelectGroup[];

interface Props {
  options: MultiSelectData;
  modelValue: string[];
  placeholder?: string;
  label?: string;
  selectionText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: "Select options...",
  label: "Options",
  selectionText: "items",
  options: () => [],
});

const emit = defineEmits<{
  "update:modelValue": [value: string[]];
}>();

// Reactive State
const isOpen = ref(false);
const filterText = ref("");
const highlightedIndex = ref(0);
const inputRef = useTemplateRef<HTMLInputElement>("inputRef");

// Core Computed Properties
const selectedCount = computed(() => props.modelValue.length);

// Detect if the options are grouped or flat
const isGrouped = computed(() => {
  return (
    props.options.length > 0 &&
    "group" in props.options[0] &&
    "items" in props.options[0]
  );
});

// Extract individual options and groups from the unified options prop
const individualOptions = computed(() => {
  if (isGrouped.value) return [];
  return props.options as MultiSelectOption[];
});

const groups = computed(() => {
  if (!isGrouped.value) return [];
  return props.options as MultiSelectGroup[];
});

// Flatten all options for easier processing
const allOptions = computed(() => {
  if (isGrouped.value) {
    return (props.options as MultiSelectGroup[]).flatMap(
      (group) => group.items
    );
  }
  return props.options as MultiSelectOption[];
});

const selectedOptions = computed(() =>
  allOptions.value.filter((option) => props.modelValue.includes(option.value))
);

// UI Helper Computed Properties
const hasSelectedImages = computed(() =>
  selectedOptions.value.some((option) => option.image)
);
const hasAnyVisualElements = computed(() => {
  return allOptions.value.some((option) => option.image || option.icon);
});

// Filtering Logic
const filteredGroups = computed(() => {
  if (!isGrouped.value) return [];

  const searchText = filterText.value.toLowerCase();

  return groups.value
    .map((group) => ({
      ...group,
      items: group.items.filter((option) => {
        // Show all items if group name matches the search
        const groupMatches = group.group.toLowerCase().includes(searchText);
        // Show individual items if their label matches the search
        const itemMatches = option.label.toLowerCase().includes(searchText);

        return groupMatches || itemMatches;
      }),
    }))
    .filter((group) => group.items.length > 0);
});

const filteredIndividualOptions = computed(() =>
  individualOptions.value.filter((option) =>
    option.label.toLowerCase().includes(filterText.value.toLowerCase())
  )
);

// All filtered options in a flat array for keyboard navigation
const filteredOptions = computed(() => {
  const individual = filteredIndividualOptions.value;
  const grouped = filteredGroups.value.flatMap((group) => group.items);
  return [...individual, ...grouped];
});

const highlightedOption = computed(
  () => filteredOptions.value[highlightedIndex.value] || null
);

// Main Interaction Methods
function toggleDropdown() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    highlightedIndex.value = 0; // Reset to first item when opening
    nextTick(() => {
      inputRef.value?.focus();
    });
  }
}

function closeDropdown() {
  isOpen.value = false;
}

function toggleOption(option: MultiSelectOption) {
  const newValue = [...props.modelValue];
  const index = newValue.indexOf(option.value);

  if (index > -1) {
    newValue.splice(index, 1);
  } else {
    newValue.push(option.value);
  }

  emit("update:modelValue", newValue);
}

function clearAll() {
  filterText.value = "";
  emit("update:modelValue", []);
}

// Keyboard Navigation
function handleInputKeydown(event: KeyboardEvent) {
  if (!isOpen.value) return;

  if (event.key === "Escape") {
    event.preventDefault();
    closeDropdown();
  } else if (event.key === "Enter" && highlightedOption.value) {
    event.preventDefault();
    event.stopPropagation();
    toggleOption(highlightedOption.value);
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    highlightedIndex.value = Math.min(
      highlightedIndex.value + 1,
      filteredOptions.value.length - 1
    );
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0);
  }
}

// Utility Functions
function renderIcon(icon: string | any) {
  if (!icon) return null;

  const iconContent =
    typeof icon === "string"
      ? h("span", { class: "text-base" }, icon)
      : h(icon, { class: "w-4 h-4" });

  return h(
    "span",
    {
      class:
        "flex-shrink-0 w-4 h-4 inline-flex items-center justify-center mr-2",
    },
    [iconContent]
  );
}

function isHighlighted(option: MultiSelectOption) {
  return highlightedOption.value?.value === option.value;
}

// Watchers
// Reset highlighted index when filter changes
watch(filterText, () => {
  highlightedIndex.value = 0;
});
</script>
