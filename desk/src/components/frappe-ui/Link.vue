<template>
  <Combobox
    class="group"
    :model-value="value || null"
    trigger="button"
    :options="linkOptions"
    :loading="options.loading"
    :filterable="false"
    :size="size"
    :variant="variant"
    :placeholder="placeholder"
    :disabled="disabled"
    :label="label"
    :description="description"
    :required="required"
    @update:model-value="(val) => (value = val)"
    @update:open="() => (text = '')"
    v-model:query="text"
  >
    <template v-if="$slots.trigger" #trigger="slotProps">
      <slot name="trigger" v-bind="slotProps" />
    </template>

    <template v-if="$slots.prefix" #prefix>
      <slot name="prefix" />
    </template>

    <template v-if="$slots['item-prefix']" #item-prefix="slotProps">
      <slot name="item-prefix" v-bind="slotProps" />
    </template>

    <template v-if="$slots['item-label']" #item-label="slotProps">
      <slot name="item-label" v-bind="slotProps" />
    </template>

    <!-- Left unfilled without a value so the chevron falls through; a filled
         field shows the clear control in its place. It renders inside the
         trigger button, so it is a span rather than a nested button. -->
    <template v-if="showClear" #suffix>
      <span
        role="button"
        tabindex="0"
        data-slot="clear"
        :aria-label="__('Clear')"
        class="hidden size-4 shrink-0 place-items-center rounded-1 text-ink-gray-5 group-hover:grid group-focus-within:grid hover:bg-surface-gray-3 hover:text-ink-gray-7 focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        @click.stop="clearValue()"
        @keydown.enter.stop.prevent="clearValue()"
        @keydown.space.stop.prevent="clearValue()"
        @pointerdown.stop
      >
        <span class="lucide-x size-3.5" />
      </span>
    </template>

    <template v-if="onCreate" #footer="{ query, setOpen }">
      <Button
        variant="ghost"
        class="w-full !justify-start"
        :label="__('Create New')"
        @click="onCreate(query, () => setOpen(false))"
      >
        <template #prefix>
          <LucidePlus class="size-4" />
        </template>
      </Button>
    </template>
  </Combobox>
</template>

<script setup>
import LucidePlus from "~icons/lucide/plus";
import { watchDebounced } from "@vueuse/core";
import { Button, Combobox, createResource } from "frappe-ui";
import { __ } from "@/translation";
import { computed, ref, useAttrs, watch } from "vue";

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  filters: {
    type: Object,
    default: null,
  },
  modelValue: {
    type: String,
    default: "",
  },
  hideMe: {
    type: Boolean,
    default: false,
  },
  pageLength: {
    type: Number,
    default: 10,
  },
  hideClearButton: {
    type: Boolean,
    default: false,
  },
  showDescription: {
    type: Boolean,
    default: false,
  },
  label: String,
  description: String,
  placeholder: String,
  required: Boolean,
  disabled: Boolean,
  size: {
    type: String,
    default: "sm",
  },
  variant: String,
  onCreate: Function,
});

const emit = defineEmits(["update:modelValue", "change"]);

const attrs = useAttrs();

const valuePropPassed = computed(() => "value" in attrs);

const value = computed({
  get: () => (valuePropPassed.value ? attrs.value : props.modelValue),
  set: (val) =>
    val && emit(valuePropPassed.value ? "change" : "update:modelValue", val),
});

// The row renderer shows `description` whenever an option carries one, so the
// field has to drop it rather than hide it.
const linkOptions = computed(() => {
  const data = options.data || [];
  const rows = props.showDescription
    ? data
    : data.map(({ description, ...rest }) => rest);
  // The button trigger prints only an option it has loaded, and the search
  // returns one page. A value saved outside that page needs a row of its own
  // or the field reads as empty.
  if (value.value && !rows.some((row) => row.value === value.value)) {
    return [{ label: value.value, value: value.value }, ...rows];
  }
  return rows;
});

// Listening to the query at all makes Combobox treat it as consumer-owned, so
// it stops resetting it (`useIsModelBound`). Opening and closing clear it here
// instead, or the label committed on select stays in the search box.
const text = ref("");

const showClear = computed(
  () => !props.disabled && !props.hideClearButton && Boolean(value.value)
);

function clearValue() {
  emit(valuePropPassed.value ? "change" : "update:modelValue", "");
  // Committing an option puts its label in the query, which is what the search
  // runs on. Clearing has to take that back out or the list stays pinned to the
  // value that was just removed.
  text.value = "";
}

function reload(val) {
  if (
    options.data?.length &&
    val === options.params?.txt &&
    props.doctype === options.params?.doctype
  )
    return;

  options.update({
    params: {
      txt: val,
      doctype: props.doctype,
      filters: props.filters,
      page_length: props.pageLength,
    },
  });
  options.reload();
}

const options = createResource({
  url: "frappe.desk.search.search_link",
  cache: [props.doctype, text.value, props.hideMe],
  method: "POST",
  params: {
    txt: text.value,
    doctype: props.doctype,
    filters: props.filters,
    page_length: props.pageLength,
  },
  transform: (data) => {
    let allData = data.map((option) => {
      return {
        value: option.value,
        label: option?.label || option.value,
        description: option?.description,
      };
    });

    if (
      !props.hideMe &&
      (props.doctype == "User" || props.doctype == "HD Agent")
    ) {
      allData.unshift({
        label: "@me",
        value: "@me",
      });
    }
    return allData;
  },
});

watchDebounced(text, (val) => reload(val || ""), {
  debounce: 300,
  immediate: true,
});

watchDebounced(
  () => props.doctype,
  () => reload(""),
  {
    debounce: 300,
    immediate: true,
  }
);

watch(
  () => props?.filters,
  (newVal) => {
    options.update({
      params: {
        txt: text.value,
        doctype: props.doctype,
        filters: newVal,
        page_length: props.pageLength,
      },
    });
    options.reload();
  },
  { deep: true }
);
</script>
