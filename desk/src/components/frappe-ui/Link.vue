<template>
  <Combobox
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
    @update:query="(query) => (text = query)"
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

    <template v-if="onCreate || !hideClearButton" #footer="{ query, setOpen }">
      <Button
        v-if="onCreate"
        variant="ghost"
        class="w-full !justify-start"
        :label="__('Create New')"
        @click="onCreate(query, () => setOpen(false))"
      >
        <template #prefix>
          <LucidePlus class="size-4" />
        </template>
      </Button>
      <Button
        v-if="!hideClearButton"
        variant="ghost"
        class="w-full !justify-start"
        :label="__('Clear')"
        @click="clearValue(() => setOpen(false))"
      >
        <template #prefix>
          <LucideX class="size-4" />
        </template>
      </Button>
    </template>
  </Combobox>
</template>

<script setup>
import LucidePlus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";
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
const linkOptions = computed(() =>
  props.showDescription
    ? options.data || []
    : (options.data || []).map(({ description, ...rest }) => rest)
);

const text = ref("");

function clearValue(close) {
  emit(valuePropPassed.value ? "change" : "update:modelValue", "");
  close();
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
