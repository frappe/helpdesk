<template>
  <div>
    <div class="flex flex-wrap gap-1">
      <Button
        ref="emailBtnRefs"
        v-for="value in values"
        :key="value"
        :label="value"
        theme="gray"
        variant="subtle"
        :class="{
          'rounded bg-surface-white hover:!bg-surface-gray-1 focus-visible:ring-outline-gray-4':
            props.variant === 'subtle',
        }"
        @keydown.delete.capture.stop="removeLastValue"
      >
        <template #suffix>
          <FeatherIcon
            class="h-3.5"
            name="x"
            @click.stop="() => removeValue(value)"
          />
        </template>
      </Button>
      <div class="flex-1">
        <Combobox v-model="selectedOptionValue" nullable>
          <Popover v-model:show="showOptions" class="w-full">
            <template #target="{ togglePopover }">
              <ComboboxInput
                ref="queryInput"
                type="text"
                :id="props.inputId"
                class="search-input form-input w-full border-none focus:border-none focus:!shadow-none focus-visible:!ring-0"
                :class="[
                  props.variant == 'ghost'
                    ? 'bg-surface-white hover:bg-surface-white'
                    : 'bg-surface-gray-2 hover:bg-surface-gray-3',
                  inputClass,
                ]"
                :placeholder="props.placeholder"
                :value="query"
                autocomplete="off"
                @change="onQueryInputChange"
                @focus="togglePopover"
                @keydown.delete.capture.stop="removeLastValue"
              />
            </template>
            <template #body="{ isOpen }">
              <div v-show="isOpen">
                <div
                  class="mt-1 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
                >
                  <ComboboxOptions
                    class="p-1.5 max-h-[12rem] overflow-y-auto"
                    static
                  >
                    <div
                      v-if="computedOptions.length === 0"
                      class="rounded px-2 py-1 text-base text-ink-gray-5"
                    >
                      {{ props.noOptionsFoundMsg }}
                    </div>
                    <ComboboxOption
                      v-for="option in computedOptions"
                      :key="option.value"
                      :value="option.value"
                      v-slot="{ active }"
                    >
                      <li
                        :class="[
                          'cursor-pointer flex items-center rounded px-2 py-1 text-base',
                          { 'bg-surface-gray-3': active },
                        ]"
                      >
                        <slot name="option" :option="option"></slot>
                      </li>
                    </ComboboxOption>
                  </ComboboxOptions>
                </div>
              </div>
            </template>
          </Popover>
        </Combobox>
      </div>
    </div>
    <ErrorMessage class="mt-2 pl-2" v-if="errorMsg" :message="errorMsg" />
    <p
      v-if="duplicateValueMsg"
      class="whitespace-pre-line text-sm text-ink-blue-3 mt-2 pl-2"
    >
      {{ duplicateValueMsg }}
    </p>
  </div>
</template>

<script setup lang="ts">
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
} from "@headlessui/vue";
import { Button, Popover, ErrorMessage } from "frappe-ui";
import { computed, nextTick, ref } from "vue";

const props = withDefaults(
  defineProps<{
    inputId: string;
    variant?: string;
    isValidValue?: (value: string) => boolean;
    getValidationErrorMsg?: (value: string) => string;
    getDuplicateValueMsg: (value: string) => string;
    options: readonly Record<"label" | "value", string>[];
    noOptionsFoundMsg: string;
    inputClass?: string;
    placeholder?: string;
    values: string[];
  }>(),
  {
    variant: "subtle",
    isValidValue: () => true,
    inputClass: "",
    placeholder: "",
  }
);

const emits = defineEmits<{ "update:values": [string[]] }>();

const query = ref("");
const emailBtnRefs = ref<InstanceType<typeof Button>[]>([]);
const showOptions = ref(false);
const errorMsg = ref("");
const duplicateValueMsg = ref("");
const queryInput = ref<InstanceType<typeof ComboboxInput> | null>(null);

const selectedOptionValue = computed<string | null>({
  get() {
    return query.value;
  },
  set(newEnteredValue) {
    showOptions.value = false;
    errorMsg.value = "";
    duplicateValueMsg.value = "";
    if (newEnteredValue === null) {
      query.value = "";
      return;
    }
    if (props.values.includes(newEnteredValue)) {
      duplicateValueMsg.value =
        props.getDuplicateValueMsg?.(newEnteredValue) ?? "";
      query.value = "";
      return;
    }
    if (!props.isValidValue(newEnteredValue)) {
      errorMsg.value = props.getValidationErrorMsg?.(newEnteredValue) ?? "";
      query.value = newEnteredValue;
      return;
    }
    emits("update:values", [...props.values, newEnteredValue]);
    query.value = "";
  },
});

const computedOptions = computed(() => {
  if (query.value === "") {
    return [];
  }
  const lowerCasedQuery = query.value.toLowerCase();
  const res = props.options.filter(
    (option) =>
      lowerCasedQuery.includes(option.label.toLowerCase()) ||
      lowerCasedQuery.includes(option.value.toLowerCase())
  );
  if (res.length === 0) {
    res.push({
      label: query.value,
      value: query.value,
    });
  }
  return res;
});

function onQueryInputChange(
  e: Event & {
    target: HTMLInputElement;
  }
) {
  query.value = e.target.value;
  showOptions.value = true;
}

function focusQueryInput() {
  queryInput.value?.$el.focus();
}

function removeLastValue() {
  if (query.value !== "") {
    return;
  }
  const lastEmailBtnRef =
    emailBtnRefs.value[emailBtnRefs.value.length - 1]?.$el;
  if (document.activeElement === lastEmailBtnRef) {
    emits("update:values", props.values.slice(0, -1));
    nextTick(() => {
      if (emailBtnRefs.value.length === 0) {
        focusQueryInput();
      } else {
        emailBtnRefs.value[emailBtnRefs.value.length - 1].$el.focus();
      }
    });
  } else {
    lastEmailBtnRef?.focus();
  }
}

function removeValue(value: string) {
  emits(
    "update:values",
    props.values.filter((v) => v !== value)
  );
}
</script>
