<template>
  <div :class="['space-y-1.5', $attrs.class as string]">
    <label v-if="label" :for="id" class="block w-fit text-xs text-ink-gray-5">
      {{ label }}
      <span v-if="required" class="text-ink-red-3">*</span>
    </label>
    <Popover v-model:open="isOpen">
      <template #target="{ togglePopover }">
        <div :class="containerClasses">
          <button
            type="button"
            class="flex h-full items-center gap-1 rounded-l px-2 focus:outline-none"
            :class="{ 'pointer-events-none': disabled }"
            :aria-label="__('Select country')"
            @click.stop="togglePopover()"
          >
            <img
              v-if="flagCode"
              :src="`https://flagcdn.com/${flagCode}.svg`"
              :alt="selectedCountry ?? ''"
              class="h-3 w-4 rounded-sm object-cover"
            />
            <FeatherIcon name="chevron-down" class="size-3.5 text-ink-gray-5" />
          </button>
          <div
            class="self-stretch border-l border-outline-gray-2"
            aria-hidden="true"
          />
          <span
            v-if="isd"
            class="select-none ps-2.5 text-base"
            :class="textColorClass"
          >
            {{ isd }}
          </span>
          <TextInput
            :id="id"
            ref="numberInputRef"
            v-model="localNumber"
            type="tel"
            variant="ghost"
            :size="size"
            :placeholder="placeholder"
            :disabled="disabled"
            :autofocus="autofocus"
            inputmode="tel"
            autocomplete="off"
            class="min-w-0 flex-1 [&_input]:!bg-transparent [&_input]:!ps-1"
            @keydown.backspace="onBackspace"
          />
          <div
            v-if="$slots.suffix"
            class="flex items-center gap-2 ps-3.5 pe-2.5"
          >
            <slot name="suffix" />
          </div>
        </div>
      </template>

      <template #body="{ close }">
        <div
          class="mt-1 flex max-h-72 w-72 flex-col overflow-hidden rounded border border-outline-gray-2 bg-surface-white shadow-md"
        >
          <div class="border-b border-outline-gray-1 p-2">
            <FormControl
              v-model="searchQuery"
              size="sm"
              autocomplete="one-time-code"
              :name="`country-search-${id}`"
              :placeholder="__('Search country')"
              :autofocus="true"
              @keydown.down.prevent="moveHighlight(1)"
              @keydown.up.prevent="moveHighlight(-1)"
              @keydown.enter.prevent="commitHighlighted(close)"
              @keydown.escape.prevent="close()"
            />
          </div>
          <div class="flex-1 overflow-y-auto py-1">
            <button
              v-for="(country, idx) in filteredCountries"
              :key="country.name"
              :ref="(el) => setItemRef(el as HTMLElement | null, idx)"
              type="button"
              class="flex w-full items-center gap-2 px-3 py-1.5 text-left text-base"
              :class="
                idx === highlightedIndex
                  ? 'bg-surface-gray-3'
                  : 'hover:bg-surface-gray-2'
              "
              @mouseenter="highlightedIndex = idx"
              @click="onSelectCountry(country.name, close)"
            >
              <img
                :src="`https://flagcdn.com/${country.code}.svg`"
                :alt="country.name"
                class="h-3 w-4 rounded-sm object-cover"
              />
              <span class="flex-1 truncate text-ink-gray-8">
                {{ country.name }}
              </span>
              <span class="text-ink-gray-5">{{ country.isd }}</span>
            </button>
            <div
              v-if="filteredCountries.length === 0"
              class="p-3 text-center text-base text-ink-gray-5"
            >
              {{ __("No country found") }}
            </div>
          </div>
        </div>
      </template>
    </Popover>
    <p v-if="description" :class="descriptionClasses">
      {{ description }}
    </p>
  </div>
</template>

<script setup lang="ts">
// TODO: replace with reka-ui in future
import { __ } from "@/translation";
import {
  createResource,
  FeatherIcon,
  FormControl,
  Popover,
  TextInput,
} from "frappe-ui";
import { computed, onMounted, ref, useId, watch } from "vue";

interface CountryInfo {
  code: string;
  isd: string;
  [key: string]: any;
}

const countryCodesResource = createResource({
  url: "frappe.geo.country_info.get_country_timezone_info",
  cache: "country-tz",
  transform: (data: any) =>
    (data?.country_info ?? data?.message?.country_info ?? data ?? {}) as Record<
      string,
      CountryInfo
    >,
});

const props = withDefaults(
  defineProps<{
    label?: string;
    placeholder?: string;
    description?: string;
    disabled?: boolean;
    required?: boolean;
    autofocus?: boolean;
    defaultCountry?: string;
    size?: "sm" | "md";
    variant?: "subtle" | "outline";
  }>(),
  {
    placeholder: "",
    disabled: false,
    required: false,
    autofocus: false,
    size: "sm",
    variant: "subtle",
  }
);

defineOptions({ inheritAttrs: false });

const model = defineModel<string>({ default: "" });

const id = useId();

const countryCodes = computed<Record<string, CountryInfo>>(
  () => countryCodesResource.data ?? {}
);
const isd = computed(
  () => countryCodes.value[selectedCountry.value ?? ""]?.isd ?? ""
);
const flagCode = computed(
  () => countryCodes.value[selectedCountry.value ?? ""]?.code ?? ""
);

const selectedCountry = ref<string | null>(null);
const localNumber = ref<string>("");
const isOpen = ref(false);
const searchQuery = ref("");
const numberInputRef = ref<{ el?: HTMLInputElement | null } | null>(null);
const highlightedIndex = ref(0);
const itemRefs: HTMLElement[] = [];

function setItemRef(el: HTMLElement | null, idx: number) {
  if (el) itemRefs[idx] = el;
}

function moveHighlight(delta: number) {
  const total = filteredCountries.value.length;
  if (total === 0) return;
  highlightedIndex.value = (highlightedIndex.value + delta + total) % total;
  itemRefs[highlightedIndex.value]?.scrollIntoView({ block: "nearest" });
}

function commitHighlighted(close: () => void) {
  const country = filteredCountries.value[highlightedIndex.value];
  if (country) onSelectCountry(country.name, close);
}

const allCountries = computed(() =>
  Object.entries(countryCodes.value)
    .filter(([, info]) => info.isd)
    .map(([name, info]) => ({ name, code: info.code, isd: info.isd }))
    .sort((a, b) => a.name.localeCompare(b.name))
);

const filteredCountries = computed(() => {
  const query = searchQuery.value.trim().toLowerCase();
  if (!query) return allCountries.value;
  return allCountries.value.filter(
    (c) => c.name.toLowerCase().includes(query) || c.isd.includes(query)
  );
});

const sizeClasses = computed(
  () =>
    ({
      sm: "h-7 rounded",
      md: "h-8 rounded",
    }[props.size])
);

const variantClasses = computed(() => {
  if (props.disabled) {
    return [
      "border bg-surface-gray-1",
      props.variant === "outline"
        ? "border-outline-gray-2"
        : "border-transparent",
    ];
  }
  return {
    subtle:
      "border border-[--surface-gray-2] bg-surface-gray-2 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus-within:bg-surface-white focus-within:border-outline-gray-4 focus-within:shadow-sm focus-within:hover:bg-surface-white focus-within:hover:border-outline-gray-4 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-outline-gray-3",
    outline:
      "border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-sm focus-within:bg-surface-white focus-within:border-outline-gray-4 focus-within:shadow-sm focus-within:hover:border-outline-gray-4 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-outline-gray-3",
  }[props.variant];
});

const containerClasses = computed(() => [
  "flex items-center w-full transition-colors",
  sizeClasses.value,
  variantClasses.value,
]);

const textColorClass = computed(() =>
  props.disabled ? "text-ink-gray-5" : "text-ink-gray-8"
);

const descriptionClasses = computed(() => [
  props.size === "md" ? "text-p-base" : "text-p-xs",
  "text-ink-gray-5",
]);

function parseValue(value: unknown) {
  const str =
    typeof value === "string"
      ? value
      : typeof value === "number"
      ? String(value)
      : "";
  const idx = str.indexOf("-");
  if (str && idx > 0) {
    const isdPart = str.substring(0, idx);
    const numberPart = str.substring(idx + 1);
    const match = Object.entries(countryCodes.value).find(
      ([, info]) => info.isd === isdPart
    );
    if (match) selectedCountry.value = match[0];
    localNumber.value = numberPart;
    return;
  }
  localNumber.value = str;
}

function getSysDefaultCountry(): string | null {
  const country = window.default_country;
  return typeof country === "string" && country ? country : null;
}

function applyDefaultCountry() {
  if (selectedCountry.value) return;
  const candidates = [props.defaultCountry, getSysDefaultCountry(), "India"];
  for (const name of candidates) {
    if (name) {
      selectedCountry.value = name;
      return;
    }
  }
}

function onSelectCountry(name: string, close: () => void) {
  selectedCountry.value = name;
  searchQuery.value = "";
  close();
  numberInputRef.value?.el?.focus();
}

function onBackspace() {
  if (!localNumber.value) selectedCountry.value = null;
}

function emitValue() {
  const number = localNumber.value;
  if (!number) {
    model.value = "";
    return;
  }
  model.value = isd.value ? `${isd.value}-${number}` : number;
}

watch([localNumber, isd], emitValue);

watch(
  () => model.value,
  (next) => {
    const current = isd.value
      ? `${isd.value}-${localNumber.value}`
      : localNumber.value;
    if (next === current) return;
    parseValue(next);
  }
);

watch(isOpen, (open) => {
  if (open) {
    highlightedIndex.value = 0;
  } else {
    searchQuery.value = "";
  }
});

watch(searchQuery, () => {
  highlightedIndex.value = 0;
  itemRefs.length = 0;
});

onMounted(async () => {
  await countryCodesResource.fetch();
  parseValue(model.value);
  if (!model.value) applyDefaultCountry();
});
</script>
