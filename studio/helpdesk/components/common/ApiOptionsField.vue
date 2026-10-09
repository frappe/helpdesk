<template>
  <Combobox
    v-model="value"
    trigger="button"
    size="sm"
    :options="options.data || []"
    :label="field.label"
    :description="field.description"
    :placeholder="field.placeholder || __('Select an option')"
    :required="field.reqd"
    :disabled="field.readOnly"
  />
</template>

<script setup lang="ts">
// The framework's FieldComponent contract, spelled out: the SFC compiler cannot resolve its types through the alias.
import { __ } from "@helpdesk/shared/translation";
import { parseApiOptions } from "@helpdesk/shared/utils";
import { Combobox, createResource } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{ field: any; modelValue: any; url: string }>();
const emit = defineEmits<{
  "update:modelValue": [value: any];
  change: [value: any];
}>();

const options = createResource({
  url: props.url,
  auto: true,
  transform: parseApiOptions,
});

const value = computed({
  get: () => props.modelValue ?? null,
  set: (next) => {
    emit("update:modelValue", next);
    emit("change", next);
  },
});
</script>
