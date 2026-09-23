<template>
  <div class="space-y-1.5" v-if="field.display_via_depends_on">
    <span class="block text-sm text-ink-gray-7">
      {{ __(field.label) }}
      <span v-if="field.required" class="place-self-center text-ink-red-6">
        *
      </span>
    </span>
    <div class="flex gap-2 items-center [&>div]:flex-1">
      <!-- model-value only: a stray `value` attr reaches the Combobox search
           input, whose native change would commit the typed search text -->
      <component
        class="w-full"
        :is="component"
        :placeholder="placeholder"
        :disabled="field.disabled"
        :model-value="transValue"
        @update:model-value="emitUpdate(field.fieldname, $event)"
        variant="outline"
      />
      <slot name="label-extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { APIOptions, Field } from "@/types";
import { parseApiOptions } from "@/utils";
import { Link } from "@framework/ui";
import {
  Combobox,
  createResource,
  DatePicker,
  DateTimePicker,
  Select,
  TextInput,
} from "frappe-ui";
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

const SEARCHABLE_FROM = 10;

// trigger: "button" keeps the search inside the popover, so the control still
// reads as a value rather than a text input
function picker(options: { label: string; value: string | number }[]) {
  return h(Combobox, { trigger: "button", options, size: "sm" });
}

// Combobox feeds one placeholder to both its trigger and its search box, so a
// short list uses Select instead: no search box, no repeated placeholder.
function select(options: { label: string; value: string | number }[]) {
  return h(Select, { options, size: "sm" });
}

function optionControl(options: { label: string; value: string | number }[]) {
  return options.length > SEARCHABLE_FROM ? picker(options) : select(options);
}

const component = computed(() => {
  if (props.field.url_method) {
    return picker(apiOptions.data || []);
  } else if (props.field.fieldtype === "Link" && props.field.options) {
    // title keeps the saved value readable until search_link returns it
    return h(Link, {
      doctype: props.field.options,
      filters: props.field.filters,
      title: props.value ? String(props.value) : undefined,
    });
  } else if (props.field.fieldtype === "Select") {
    return optionControl(
      props.field.options
        ? props.field.options.split("\n").map((o) => ({ label: o, value: o }))
        : []
    );
  } else if (props.field.fieldtype === "Check") {
    return select([
      { label: "Yes", value: 1 },
      { label: "No", value: 0 },
    ]);
  } else if (props.field.fieldtype === "Datetime") {
    return h(DateTimePicker, {
      format: `${window.date_format.toUpperCase()} ${window.time_format}`,
    });
  } else if (props.field.fieldtype === "Date") {
    return h(DatePicker, {
      id: props.field.fieldname,
      format: window.date_format.toUpperCase(),
    });
  } else {
    return h(TextInput, {
      debounce: 100,
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
    // the picker matches on option value, so keep the stored 1 / 0
    return props.value ? 1 : 0;
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
    props.field.fieldtype === "Link" ||
    props.field.fieldtype === "Check"
  ) {
    return "Select an option";
  }
  return "Type something";
});

function emitUpdate(fieldname: Field["fieldname"], value: Value) {
  emit("change", { fieldname, value });
}
</script>
