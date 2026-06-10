<template>
  <div class="flex flex-col">
    <div
      class="flex h-9 items-center justify-between gap-1 border-b border-outline-gray-1 pe-2"
    >
      <BackButton
        :label="field.label"
        size="sm"
        class="min-w-0"
        @back="emit('back')"
      />
      <Dropdown side="bottom" :options="operatorOptions">
        <Button
          :title="operatorLabel"
          class="flex h-6 max-w-[150px] shrink-0 items-center gap-1 rounded bg-surface-gray-2 ps-2 pe-1 text-sm text-ink-gray-7 hover:bg-surface-gray-3"
          variant="ghost"
          icon-right="lucide-chevron-down"
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
        </TextInput>
      </div>
      <div ref="listEl" class="mt-1 max-h-52 overflow-y-auto p-1.5 py-1">
        <button
          v-for="(option, index) in options"
          :key="option.value"
          :data-index="index"
          :class="[
            'flex h-8 w-full items-center gap-2 rounded px-1.5 text-base text-ink-gray-8',
            index === activeIndex ? 'bg-surface-gray-2' : '',
          ]"
          @mousemove="activeIndex = index"
          @click="pickOption(option.value)"
        >
          <span class="flex-1 truncate text-start">{{ option.label }}</span>
          <LucideCheck
            v-if="isSelected(option.value)"
            class="size-4 text-ink-gray-7"
          />
        </button>
        <div
          v-if="!options.length"
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
        @change="(v) => applyValue(splitRange(v))"
      />
      <component
        v-else-if="isDate"
        :is="field.fieldtype === 'Date' ? DatePicker : DateTimePicker"
        :value="value"
        icon-left=""
        @change="(v) => applyValue(v)"
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
import {
  ActiveFilter,
  FilterField,
  useFilterCore,
  useLinkSearch,
} from "./filterCore";

interface P {
  field: FilterField;
  filter?: ActiveFilter | null;
}

interface E {
  (event: "apply", operator: string, value: any): void;
  (event: "clear"): void;
  (event: "back"): void;
}

const props = withDefaults(defineProps<P>(), { filter: null });
const emit = defineEmits<E>();

const core = useFilterCore();
const { getOperators, getDefaultOperator, getSelectOptions, timespanOptions } =
  core;

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
    ].filter((o) => matches(o.label));
  }
  if (isDate.value) return timespanOptions.filter((o) => matches(o.label));
  if (isLink.value) return linkSearch.results.data || [];
  const values =
    props.field.fieldtype === "Check"
      ? ["Yes", "No"]
      : getSelectOptions(props.field.options);
  return values.filter(matches).map((v) => ({ label: v, value: v }));
});

const dateRangeValue = computed(() =>
  Array.isArray(value.value) ? value.value.join(",") : ""
);

const linkSearch = useLinkSearch(linkDoctype(props.field));

function linkDoctype(field: FilterField): string {
  if (field.fieldname === "_assign") return "User";
  return field.fieldtype === "Link" ? field.options || "" : "";
}

function defaultValueFor(op: string): any {
  return ["in", "not in"].includes(op) ? [] : "";
}

function plainText(v: any): string {
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "string") return v.replaceAll("%", "");
  return v == null ? "" : String(v);
}

function isSelected(option: string): boolean {
  if (Array.isArray(value.value)) return value.value.includes(option);
  return plainText(value.value) === String(option);
}

function pickOption(option: string) {
  if (!isMultiple.value) {
    applyValue(option);
    return;
  }
  const current = Array.isArray(value.value) ? [...value.value] : [];
  const index = current.indexOf(option);
  index === -1 ? current.push(option) : current.splice(index, 1);
  value.value = current;
  if (!current.length) {
    emit("clear");
    return;
  }
  emit("apply", operator.value, [...current]);
  search.value = "";
  focusSearch();
}

function applyValue(v: any) {
  value.value = v;
  emit("apply", operator.value, v);
}

function splitRange(v: any): string[] {
  if (typeof v !== "string") return v;
  const [start, end] = v.split(",");
  return [start, end];
}

function onKeydown(event: KeyboardEvent) {
  if (event.isComposing) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    event.stopPropagation();
    const delta = event.key === "ArrowDown" ? 1 : -1;
    const total = options.value.length;
    if (total) activeIndex.value = (activeIndex.value + delta + total) % total;
  } else if (event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;
    const option = options.value[activeIndex.value];
    if (option) pickOption(option.value);
  } else if (event.key === "Backspace" && !search.value) {
    event.stopPropagation();
    emit("back");
  }
}

function focusSearch() {
  nextTick(() => (searchInput.value || valueInput.value)?.el?.focus());
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
  const v = isMultiple.value
    ? textValue.value.split(",").map((part: string) => part.trim())
    : textValue.value;
  applyValue(v);
}, 500);

function hasValue(v: any): boolean {
  if (Array.isArray(v)) return v.length > 0;
  return v !== "" && v != null;
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
  value.value = convertValue(value.value);
  textValue.value = plainText(value.value);
  if (hasValue(value.value)) emit("apply", newOperator, value.value);
});

function convertValue(v: any): any {
  if (!isMultiple.value) return Array.isArray(v) ? v[0] || "" : plainText(v);
  if (Array.isArray(v)) return v;
  const single = plainText(v);
  return single ? [single] : [];
}

watch(
  () => isListMode.value,
  () => {
    focusSearch();
  },
  { immediate: true }
);

function cycleOperator() {
  const list = operators.value;
  if (list.length < 2) return;
  const currentIndex = list.findIndex((o) => o.value === operator.value);
  operator.value = list[(currentIndex + 1) % list.length].value;
}

useEventListener(document, "keydown", (event: KeyboardEvent) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "e") {
    event.preventDefault();
    cycleOperator();
    return;
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
