<template>
  <div class="flex flex-col">
    <div
      class="flex h-9 items-center justify-between gap-1 border-b border-outline-gray-1 pe-2 ps-1"
    >
      <BackButton
        :label="field.label"
        size="sm"
        class="min-w-0"
        @back="emit('back')"
      />
      <Dropdown side="bottom" :options="operatorOptions">
        <Button
          class="flex h-6 max-w-[150px] shrink-0 items-center gap-1 rounded bg-surface-gray-2 ps-2 pe-1 text-sm text-ink-gray-7 hover:bg-surface-gray-3"
          variant="ghost"
          icon-right="lucide-chevron-down"
          :tooltip="operatorTooltip"
        >
          <span class="min-w-0 truncate">{{ operatorLabel }}</span>
        </Button>
        <template #item-suffix="{ selected }">
          <LucideCheck v-if="selected" class="size-4 text-ink-gray-7" />
        </template>
      </Dropdown>
    </div>
    <template v-if="isListMode">
      <div v-if="showSearch" class="px-2 pt-2">
        <TextInput
          ref="searchInput"
          v-model="search"
          type="text"
          variant="outline"
          :placeholder="__('Search...')"
          autocomplete="off"
          @keydown="onKeydown"
        >
          <template #prefix>
            <LucideSearch class="size-4 text-ink-gray-5" />
          </template>
          <template v-if="isSearching" #suffix>
            <LucideLoaderCircle class="size-4 animate-spin text-ink-gray-5" />
          </template>
        </TextInput>
      </div>
      <div
        ref="listEl"
        role="listbox"
        :aria-label="field.label"
        class="mt-1 max-h-52 overflow-y-auto p-1.5 py-1"
      >
        <button
          v-for="(option, index) in options"
          :key="option.value"
          :data-index="index"
          role="option"
          :aria-selected="isSelected(option.value)"
          :class="[
            'flex h-8 w-full items-center gap-2 rounded px-1.5 text-base text-ink-gray-8',
            index === activeIndex ? 'bg-surface-gray-2' : '',
          ]"
          @mousemove="activeIndex = index"
          @click="pickOption(option.value)"
        >
          <span :title="option.label" class="flex-1 truncate text-start">{{
            option.label
          }}</span>
          <LucideCheck
            v-if="isSelected(option.value)"
            class="size-4 text-ink-gray-7"
          />
        </button>
        <div
          v-if="isSearching && !options.length"
          class="flex h-8 items-center gap-2 px-2 text-base text-ink-gray-5"
        >
          <LucideLoaderCircle class="size-4 animate-spin" />
          {{ __("Searching...") }}
        </div>
        <div
          v-else-if="!options.length"
          class="flex h-8 items-center px-2 text-base text-ink-gray-5"
        >
          {{ __("No results") }}
        </div>
      </div>
    </template>
    <div v-else class="flex flex-col gap-2 p-2">
      <div v-if="isRatingPicker" class="px-2 py-1">
        <Rating v-model="ratingStars" />
      </div>
      <DateRangePicker
        v-else-if="isDate && operator === 'between'"
        :value="dateRangeValue"
        icon-left=""
        @change="handleDateRange"
      />
      <component
        v-else-if="isDate"
        :is="field.fieldtype === 'Date' ? DatePicker : DateTimePicker"
        :value="value"
        icon-left=""
        @change="(date) => commitAndClose(date)"
      />
      <TextInput
        v-else
        ref="valueInput"
        :type="isNumber ? 'number' : 'text'"
        v-model="textValue"
        :placeholder="isMultiple ? __('Comma separated values') : __('Value')"
        @update:model-value="onTextChange"
        @keydown="onTextKeydown"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import BackButton from "@/components/BackButton.vue";
import { useDevice } from "@/composables";
import { __ } from "@/translation";
import { useDebounceFn, useEventListener } from "@vueuse/core";
import {
  DatePicker,
  DateRangePicker,
  DateTimePicker,
  Dropdown,
  Rating,
  TextInput,
} from "frappe-ui";
import { computed, nextTick, ref, watch } from "vue";
import { ActiveFilter, FilterField, useFilter, useLinkSearch } from "./filter";

interface P {
  field: FilterField;
  filter?: ActiveFilter | null;
}

interface E {
  (event: "apply", operator: string, value: any): void;
  (event: "clear"): void;
  (event: "back"): void;
  (event: "done"): void;
}

const props = withDefaults(defineProps<P>(), { filter: null });
const emit = defineEmits<E>();

const { getOperators, getDefaultOperator, getSelectOptions, timespanOptions } =
  useFilter();

const operator = ref(props.filter?.operator || getDefaultOperator(props.field));
const value = ref(props.filter?.value ?? defaultValueFor(operator.value));
const textValue = ref(plainText(value.value));
const search = ref("");
const activeIndex = ref(0);
const searchInput = ref(null);
const valueInput = ref(null);
const listEl = ref<HTMLElement | null>(null);

const operators = computed(() =>
  getOperators(props.field.fieldtype, props.field.fieldname)
);
const operatorLabel = computed(
  () =>
    operators.value.find((option) => option.value === operator.value)?.label ||
    operator.value
);
const { isMac } = useDevice();
const operatorTooltip = __("Change operator ({0})", isMac ? "⌥↓/↑" : "Alt+↓/↑");
const operatorOptions = computed(() =>
  operators.value.map((option) => ({
    label: option.label,
    selected: option.value === operator.value,
    onClick: () => (operator.value = option.value),
  }))
);
const isDate = computed(() =>
  ["Date", "Datetime"].includes(props.field.fieldtype)
);
const isNumber = computed(() =>
  ["Float", "Int", "Currency", "Percent"].includes(props.field.fieldtype)
);
const isLink = computed(
  () => props.field.fieldtype === "Link" || props.field.fieldname === "_assign"
);
const isMultiple = computed(() => ["in", "not in"].includes(operator.value));

// Rating uses the star picker for every operator except "is" (set / not set).
// Ratings are stored as a 0..1 fraction, so convert to/from star units (×5).
const isRatingPicker = computed(
  () => props.field.fieldtype === "Rating" && operator.value !== "is"
);
const ratingStars = computed({
  get: () => Math.round((Number(value.value) || 0) * 5),
  set: (stars: number) => applyValue(stars / 5),
});

const isListMode = computed(() => {
  if (operator.value === "is") return true;
  if (isDate.value) return operator.value === "timespan";
  if (["Select", "Check"].includes(props.field.fieldtype)) {
    return true;
  }
  // "like" matches free text, so it gets a plain input; only the assignee
  // picker keeps its user list since "like" is its primary operator
  if (props.field.fieldname === "_assign") return true;
  return isLink.value && !operator.value.includes("like");
});

// "is" only offers Set / Not Set, so the search box is just noise there
const showSearch = computed(() => isListMode.value && operator.value !== "is");

const options = computed<Array<{ label: string; value: string }>>(() => {
  const matches = (label: string) =>
    label.toLowerCase().includes(search.value.toLowerCase());

  if (operator.value === "is") {
    return [
      { label: __("Set"), value: "set" },
      { label: __("Not Set"), value: "not set" },
    ].filter((option) => matches(option.label));
  }
  if (isDate.value)
    return timespanOptions.filter((option) => matches(option.label));
  if (isLink.value) return linkSearch.results.data || [];
  const values =
    props.field.fieldtype === "Check"
      ? ["Yes", "No"]
      : getSelectOptions(props.field.options);
  return values
    .filter(matches)
    .map((option) => ({ label: option, value: option }));
});

const dateRangeValue = computed(() =>
  Array.isArray(value.value) ? value.value : []
);

const linkSearch = useLinkSearch(linkDoctype(props.field));

// Link options are fetched from the server, so reflect the in-flight request
// instead of briefly showing "No results" while the search is loading.
const isSearching = computed(() => isLink.value && linkSearch.results.loading);

function linkDoctype(field: FilterField): string {
  if (field.fieldname === "_assign") return "User";
  return field.fieldtype === "Link" ? field.options || "" : "";
}

function defaultValueFor(operatorName: string): any {
  return ["in", "not in"].includes(operatorName) ? [] : "";
}

function plainText(rawValue: any): string {
  if (Array.isArray(rawValue)) return rawValue.join(", ");
  if (typeof rawValue === "string") return rawValue.replaceAll("%", "");
  return rawValue == null ? "" : String(rawValue);
}

function isSelected(option: string): boolean {
  if (Array.isArray(value.value)) return value.value.includes(option);
  return plainText(value.value) === String(option);
}

function pickOption(option: string) {
  if (!isMultiple.value) {
    // A single-select pick (Equals/Not Equals, Is, Timespan, single assignee)
    // completes the filter in one click, so return to the overview.
    commitAndClose(option);
    return;
  }
  const selectedValues = Array.isArray(value.value) ? [...value.value] : [];
  const index = selectedValues.indexOf(option);
  index === -1 ? selectedValues.push(option) : selectedValues.splice(index, 1);
  value.value = selectedValues;
  if (!selectedValues.length) {
    emit("clear");
    return;
  }
  emit("apply", operator.value, [...selectedValues]);
  search.value = "";
  focusSearch();
}

function applyValue(nextValue: any) {
  value.value = nextValue;
  emit("apply", operator.value, nextValue);
}

// A discrete pick (single list option, date, or range) fully sets the value, so
// the filter is complete — apply it and return to the overview. Incremental
// inputs (multi-select, typing, rating) keep using applyValue and stay put.
function commitAndClose(nextValue: any) {
  applyValue(nextValue);
  emit("done");
}

// The range picker emits an empty array when its selection is cleared
function handleDateRange(emittedRange: any) {
  const range = splitRange(emittedRange);
  if (!Array.isArray(range) || !range[0] || !range[1]) {
    emit("clear");
    return;
  }
  commitAndClose(range);
}

function splitRange(rawRange: any): string[] {
  if (!Array.isArray(rawRange) && typeof rawRange !== "string") return [];
  if (Array.isArray(rawRange)) return rawRange;
  const delimiter = rawRange.includes(" to ") ? " to " : ",";
  return rawRange.split(delimiter).map((s) => s.trim());
}

function moveActive(delta: number) {
  const total = options.value.length;
  if (total) activeIndex.value = (activeIndex.value + delta + total) % total;
}

function selectActive() {
  const option = options.value[activeIndex.value];
  if (option) pickOption(option.value);
}

function onKeydown(event: KeyboardEvent) {
  if (event.isComposing) return;
  // Let ⌥↑/⌥↓ bubble to the operator-cycle handler instead of moving the list.
  if (event.altKey) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    event.stopPropagation();
    moveActive(event.key === "ArrowDown" ? 1 : -1);
  } else if (event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;
    selectActive();
  } else if (event.key === "Backspace" && !search.value) {
    event.stopPropagation();
    emit("back");
  }
}

function focusSearch() {
  // preventScroll: the panel mounts mid-swipe, still translated; a default
  // focus would scroll it into view and visually cancel the slide
  nextTick(() =>
    (searchInput.value || valueInput.value)?.el?.focus({ preventScroll: true })
  );
}

function onTextKeydown(event: KeyboardEvent) {
  if (event.key === "Backspace" && !textValue.value) {
    event.stopPropagation();
    emit("back");
  }
}

function onTextChange() {
  if (!textValue.value) {
    // an empty value removes the condition right away, so going back
    // before the debounce fires can't leave a stale filter behind
    value.value = defaultValueFor(operator.value);
    emit("clear");
    return;
  }
  debouncedTextApply();
}

const debouncedTextApply = useDebounceFn(() => {
  if (!textValue.value) return;
  const nextValue = isMultiple.value
    ? textValue.value.split(",").map((part: string) => part.trim())
    : textValue.value;
  applyValue(nextValue);
}, 500);

function hasValue(candidate: any): boolean {
  if (Array.isArray(candidate)) return candidate.length > 0;
  return candidate !== "" && candidate != null;
}

watch(search, () => {
  activeIndex.value = 0;
  if (isLink.value) linkSearch.search(search.value);
});

watch(activeIndex, (index) => {
  nextTick(() => {
    listEl.value
      ?.querySelector(`[data-index="${index}"]`)
      ?.scrollIntoView({ block: "nearest" });
  });
});

watch(operator, (newOperator, oldOperator) => {
  search.value = "";
  activeIndex.value = 0;
  if (newOperator === "is") {
    applyValue("set");
    return;
  }
  if (oldOperator === "is") {
    value.value = defaultValueFor(newOperator);
    textValue.value = "";
    return;
  }
  if (
    isDate.value &&
    dateValueKind(newOperator) !== dateValueKind(oldOperator)
  ) {
    value.value = defaultValueFor(newOperator);
    textValue.value = "";
    return;
  }
  value.value = convertValue(value.value);
  textValue.value = plainText(value.value);
  if (hasValue(value.value)) emit("apply", newOperator, value.value);
});

// Date value shape per operator; a value can only carry across same-shape switches.
function dateValueKind(operatorName: string): string {
  if (operatorName === "timespan") return "timespan";
  if (operatorName === "between") return "range";
  return "scalar";
}

function convertValue(rawValue: any): any {
  if (!isMultiple.value)
    return Array.isArray(rawValue) ? rawValue[0] || "" : plainText(rawValue);
  if (Array.isArray(rawValue)) return rawValue;
  const single = plainText(rawValue);
  return single ? [single] : [];
}

watch(
  () => isListMode.value,
  () => {
    focusSearch();
  },
  { immediate: true }
);

function cycleOperator(direction: number) {
  const operatorList = operators.value;
  if (operatorList.length < 2) return;
  const currentIndex = operatorList.findIndex(
    (option) => option.value === operator.value
  );
  const total = operatorList.length;
  operator.value =
    operatorList[(currentIndex + direction + total) % total].value;
}

useEventListener(document, "keydown", (event: KeyboardEvent) => {
  // ⌥↓ / ⌥↑ (Alt on Windows) steps to the next / previous operator. A modifier
  // is required because a value input is usually focused and would swallow a
  // bare arrow key.
  if (event.altKey && (event.key === "ArrowDown" || event.key === "ArrowUp")) {
    event.preventDefault();
    cycleOperator(event.key === "ArrowDown" ? 1 : -1);
    return;
  }
  // List modes without a search box ("Is" → Set / Not Set) have no input to
  // catch arrow keys, so drive the option list straight from the document.
  if (isListMode.value && !showSearch.value) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      moveActive(event.key === "ArrowDown" ? 1 : -1);
      return;
    }
    if (event.key === "Enter" && !event.repeat) {
      event.preventDefault();
      selectActive();
      return;
    }
  }
  // Backspace goes back — except while typing in a field, where the input's own
  // handler manages an empty-Backspace and otherwise deletes characters.
  if (event.key === "Backspace") {
    const el = document.activeElement;
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement) {
      return;
    }
    event.preventDefault();
    emit("back");
  }
});
</script>
