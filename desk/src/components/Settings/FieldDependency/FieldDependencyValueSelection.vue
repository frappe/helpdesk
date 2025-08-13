<template>
  <div
    class="flex w-full flex-1 justify-between h-full h-[420px] max-h-[420px] min-h-[420px]"
  >
    <!-- left box -->
    <div class="flex-1 flex flex-col gap-1.5">
      <span class="block text-xs text-ink-gray-5">
        Select parent field value
      </span>
      <div class="border flex-1 border-r-0 rounded-l p-2 flex flex-col gap-2">
        <template v-if="state.selectedParentField">
          <FormControl
            v-model="state.parentSearch"
            :placeholder="parentPlaceholder"
            type="text"
            class="w-full"
          >
            <template #prefix>
              <LucideSearch class="h-4 w-4 text-gray-500" />
            </template>
          </FormControl>
          <div class="flex-1 overflow-y-auto hide-scrollbar basis-0">
            <ul class="max-w-[350px] overflow-y-auto">
              <li
                v-for="value in filteredParentFieldValues"
                :key="value"
                class="py-2 mb-1 px-2.5 cursor-pointer rounded flex justify-between items-center hover:bg-surface-gray-1 overflow-hidden max-w-full"
                :class="{
                  'bg-surface-gray-2 hover:bg-surface-gray-3':
                    state.currentParentSelection === value,
                }"
                @click="handleParentValueClick(value)"
              >
                <span class="text-base text-ink-gray-6 max-w-[90%] truncate">{{
                  value
                }}</span>
                <LucideChevronRight
                  class="h-4 w-4 text-ink-gray-6"
                  v-if="
                    getSelectedChildValueCount(value) === 0 ||
                    state.currentParentSelection === value
                  "
                />
                <Badge
                  v-else
                  :label="getSelectedChildValueCount(value)"
                  :theme="'gray'"
                  variant="subtle"
                  class="!h-4"
                />
              </li>
            </ul>
          </div>
        </template>
        <template v-else>
          <div
            class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
          >
            Please select a parent field first
          </div>
        </template>
      </div>
    </div>
    <!-- right box -->
    <div class="flex-1 flex flex-col gap-1.5">
      <span class="block text-xs text-ink-gray-5 pl-1.5">
        Select child field value
      </span>
      <div class="border flex-1 rounded-r p-2 flex flex-col gap-2">
        <template
          v-if="state.selectedChildField && state.currentParentSelection"
        >
          <FormControl
            v-model="state.childSearch"
            :placeholder="childPlaceholder"
            type="text"
            class="w-full"
          >
            <template #prefix>
              <LucideSearch class="h-4 w-4 text-gray-500" />
            </template>
          </FormControl>
          <div class="flex-1 overflow-y-auto hide-scrollbar basis-0">
            <!-- Master Check box -->
            <li
              class="py-2 mb-1 px-2.5 cursor-pointer rounded flex items-center bg-surface-gray-1 hover:bg-surface-gray-2"
              @click="handleSelectAllChildValues(!toggleAllChildValues)"
            >
              <FormControl
                type="checkbox"
                :model-value="toggleAllChildValues"
                class="mr-2"
              />
              <span class="text-base text-ink-gray-8 font-medium">
                {{ toggleCheckboxLabel }}
              </span>
            </li>
            <ul class="max-w-[350px] overflow-y-auto">
              <li
                v-for="value in filteredChildFieldValues"
                :key="value"
                class="py-2 mb-1 px-2.5 cursor-pointer rounded flex items-center hover:bg-surface-gray-1 max-w-full truncate"
                @click="handleChildValueClick(value)"
              >
                <FormControl
                  type="checkbox"
                  :model-value="isChildValueSelected(value)"
                  class="mr-2"
                />
                <span class="text-base text-ink-gray-6">{{ value }}</span>
              </li>
            </ul>
          </div>
        </template>
        <template v-else-if="!state.selectedChildField">
          <div
            class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
          >
            Please select a child field first
          </div>
        </template>
        <template v-else>
          <div
            class="flex flex-col items-center mt-20 h-full text-ink-gray-4 text-sm"
          >
            Please select a parent value first
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { FieldCriteriaState } from "@/types";
import { computed } from "vue";

const props = defineProps<{
  isNew: boolean;
  parentFields: any[];
}>();

const state = defineModel<FieldCriteriaState>();

const filteredParentFieldValues = computed(() => {
  if (!state.value.parentSearch) return state.value.parentFieldValues;
  return state.value.parentFieldValues.filter((v) =>
    v.toLowerCase().includes(state.value.parentSearch.toLowerCase())
  );
});

const filteredChildFieldValues = computed(() => {
  if (!state.value.childSearch) return state.value.childFieldValues;
  return state.value.childFieldValues.filter((v) =>
    v.toLowerCase().includes(state.value.childSearch.toLowerCase())
  );
});

const parentPlaceholder = computed(() => {
  if (!state.value.selectedParentField) return "Search values";
  let label = props.parentFields.find(
    (f) => f.value === state.value.selectedParentField
  )?.label;
  return `Search ${label} values`;
});
const childPlaceholder = computed(() => {
  if (!state.value.currentParentSelection) return "Search values";
  return `Search ${state.value.currentParentSelection} values`;
});

function handleParentValueClick(value: string) {
  state.value.currentParentSelection = value;
}

function handleChildValueClick(childValue: string) {
  const parent = state.value.currentParentSelection;
  if (!parent) return;
  if (!(state.value.childSelections[parent] instanceof Set)) {
    state.value.childSelections[parent] = new Set();
  }
  if (state.value.childSelections[parent].has(childValue)) {
    state.value.childSelections[parent].delete(childValue);
  } else {
    state.value.childSelections[parent].add(childValue);
  }
}

function getSelectedChildValueCount(parent: string) {
  const selectedCount =
    state.value.childSelections[parent] instanceof Set
      ? state.value.childSelections[parent].size
      : 0;
  return selectedCount;
}

// Toggling master checkbox + child values
const toggleAllChildValues = computed({
  get() {
    const parent = state.value.currentParentSelection;
    if (!parent) return false;
    // If no child values are selected, return false
    if (!(state.value.childSelections[parent] instanceof Set)) {
      return false;
    }
    // If all filtered child values are selected, return true
    return (
      state.value.childSelections[parent].size ===
      filteredChildFieldValues.value.length
    );
  },
  set(value) {
    handleSelectAllChildValues(value);
  },
});

const toggleCheckboxLabel = computed(() => {
  const parent = state.value.currentParentSelection;
  if (!parent) return "Select All";
  const selectedCount = getSelectedChildValueCount(parent);
  if (selectedCount === 0) return "Select All";
  return `${selectedCount} ${
    selectedCount === 1 ? "value" : "values"
  } selected`;
});

function handleSelectAllChildValues(value: boolean) {
  const parent = state.value.currentParentSelection;
  if (!parent) return;

  if (!(state.value.childSelections[parent] instanceof Set)) {
    state.value.childSelections[parent] = new Set();
  }

  if (value) {
    // Select all child values
    filteredChildFieldValues.value.forEach((childValue) => {
      state.value.childSelections[parent].add(childValue);
    });
  } else {
    // Deselect all child values
    state.value.childSelections[parent].clear();
  }
}

function isChildValueSelected(childValue: string) {
  const parent = state.value.currentParentSelection;
  return (
    state.value.childSelections[parent] instanceof Set &&
    state.value.childSelections[parent].has(childValue)
  );
}
</script>

<style scoped></style>
