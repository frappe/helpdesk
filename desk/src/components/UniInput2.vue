<template>
  <div class="flex items-center gap-2 px-6 pb-1 leading-5 first:mt-3">
    <div class="w-[106px] shrink-0 text-sm text-gray-600">
      {{ field.label }}
      <span v-if="field.required" class="text-red-500"> * </span>
    </div>
    <div class="min-h-[28px] flex-1 items-center overflow-hidden text-base">
      <component
        :is="component"
        class="form-control"
        :placeholder="`Add ${field.label}`"
        :value="transValue"
        :model-value="transValue"
        @update:model-value="emitUpdate(field.fieldname, $event)"
        @change="emitUpdate(field.fieldname, $event.value || $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from "vue";
import { Autocomplete } from "@/components";
import { createResource, FormControl } from "frappe-ui";
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
<style scoped>
:deep(.form-control input:not([type="checkbox"])),
:deep(.form-control select),
:deep(.form-control textarea),
:deep(.form-control button) {
  border-color: transparent;
  background: white;
}

:deep(.form-control button) {
  gap: 0;
}
:deep(.form-control [type="checkbox"]) {
  margin-left: 9px;
  cursor: pointer;
}

:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.form-control button svg) {
  color: white;
  width: 0;
}
</style>