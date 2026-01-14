<template>
  <div class="space-y-1.5" v-if="field.display_via_depends_on">
    <span class="block text-sm text-gray-700">
      {{ field.label }}
      <span v-if="field.required" class="place-self-center text-red-500">
        *
      </span>
    </span>
    <div class="flex gap-2 items-center">   
      <component
      :is="component"
      :placeholder="placeholder"
      :value="transValue"
      :disabled="field.disabled"
      :model-value="transValue"
      @update:model-value="emitUpdate(field.fieldname, $event)"
      @change="
        emitUpdate(
          field.fieldname,
          $event.target?.value || $event.value || $event
        )
      "
    />
    <slot name="label-extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Autocomplete  } from "@/components";
import { APIOptions, Field } from "@/types";
import { parseApiOptions } from "@/utils";
import { createResource, FormControl } from "frappe-ui";
import { Link }  from "frappe-ui/frappe"
import { computed, h } from "vue";

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
  console.log("FIELD", props.field);
  if (props.field.url_method) {
    return h(Autocomplete, {
      options: apiOptions.data,
      size: "sm",
    });
  } else if (props.field.fieldtype === "Link" && props.field.options) {
    return h(Link, {
      doctype: props.field.options,
      filters: props.field.filters,
    });
  } else if (props.field.fieldtype === "Select") {
    return h(Autocomplete, {
      options: props.field.options
        .split("\n")
        .map((o) => ({ label: o, value: o })),
      size: "sm",
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
      size: "sm",
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
  transform: (data: APIOptions) => {
    return parseApiOptions(data);
  },
});

const transValue = computed(() => {
  if (props.field.fieldtype === "Check") {
    return props.value ? "Yes" : "No";
  }
  return props.value;
});

const placeholder = computed(() => {
  if (props.field.placeholder) {
    return props.field.placeholder;
  }
  if (props.field.fieldtype === "Data" && !props.field.url_method) {
    return "Type something";
  } else if (
    props.field.fieldtype === "Select" ||
    props.field.fieldtype === "Link"
  ) {
    return "Select an option";
  }
  return "Type something";
});

function emitUpdate(fieldname: Field["fieldname"], value: Value) {
  emit("change", { fieldname, value });
}
</script>
