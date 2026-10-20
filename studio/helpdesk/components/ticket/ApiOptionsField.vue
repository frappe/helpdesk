<template>
  <Combobox
    v-model="value"
    trigger="button"
    size="sm"
    :options="list"
    :label="field.label"
    :description="field.description"
    :placeholder="field.placeholder || __('Select an option')"
    :required="field.reqd"
    :disabled="field.readOnly"
  />
</template>

<script setup lang="ts">
// Props inlined: the SFC compiler can't resolve FieldComponent via the alias.
import { __ } from "@helpdesk/shared/translation";
import { parseApiOptions } from "@helpdesk/shared/utils";
import { Combobox, createResource } from "frappe-ui";
import { computed } from "vue";

// `url` fetches the options; `options` passes a long Select's own, to search.
const props = defineProps<{
  field: any;
  modelValue: any;
  url?: string;
  options?: { label: string; value: string }[];
}>();
const emit = defineEmits<{
  "update:modelValue": [value: any];
  change: [value: any];
}>();

const fetched = createResource({
  url: props.url,
  auto: Boolean(props.url),
  transform: parseApiOptions,
});
const list = computed(() => props.options ?? fetched.data ?? []);

const value = computed({
  get: () => props.modelValue ?? null,
  set: (next) => {
    emit("update:modelValue", next);
    emit("change", next);
  },
});
</script>
