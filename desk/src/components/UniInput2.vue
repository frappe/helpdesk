<template>
  <div class="flex items-center gap-2 px-6 pb-1 leading-5 first:mt-3">
    <div class="w-[106px] shrink-0 text-sm text-gray-600">
      {{ field.label }}
      <span v-if="field.required" class="text-red-500"> * </span>
    </div>
    <component
      :is="component"
      :placeholder="field.placeholder || `Add ${field.label}`"
      :value="transValue"
      :model-value="transValue"
      @update:model-value="emitUpdate(field.fieldname, $event)"
      @change="emitUpdate(field.fieldname, $event.value || $event)"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h } from "vue";
import { createResource, Autocomplete, FormControl } from "frappe-ui";
import { Field } from "@/types";
import SearchComplete from "./SearchComplete.vue";

type Value = string | number | boolean;

interface P {
  field: Field;
  value: Value;
}

interface R {
  fieldname: Field["fieldname"];
  value: Value;
}

interface E {
  (event: "change", value: R);
}

const props = defineProps<P>();
const emit = defineEmits<E>();

const component = computed(() => {
  if (props.field.url_method) {
    return h(Autocomplete, {
      options: apiOptions.data,
    });
  } else if (props.field.fieldtype === "Link" && props.field.options) {
    return h(SearchComplete, {
      doctype: props.field.options,
    });
  } else if (props.field.fieldtype === "Select") {
    return h(Autocomplete, {
      options: props.field.options
        .split("\n")
        .map((o) => ({ label: o, value: o })),
    });
  } else if (props.field.fieldtype === "Check") {
    return h(Autocomplete, {
      options: [
        {
          label: "Yes",
          value: 1,
        },
        {
          label: "No",
          value: 0,
        },
      ],
    });
  } else {
    return h(FormControl, {
      debounce: 500,
    });
  }
});

const apiOptions = createResource({
  url: props.field.url_method,
  auto: !!props.field.url_method,
  transform: (data) =>
    data.map((o) => ({
      label: o,
      value: o,
    })),
});

const transValue = computed(() => {
  if (props.field.fieldtype === "Check") {
    return props.value ? "Yes" : "No";
  }
  return props.value;
});

function emitUpdate(fieldname: Field["fieldname"], value: Value) {
  emit("change", { fieldname, value });
}
</script>