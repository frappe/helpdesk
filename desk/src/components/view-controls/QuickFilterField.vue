<template>
  <FormControl
    v-if="filter.type == 'Check'"
    :label="filter.label"
    type="checkbox"
    :checked="props.value"
    @change.stop="updateFilter(filter, $event.target.checked)"
    class="!min-w-36 max-w-36"
  />
  <FormControl
    v-else-if="filter.type === 'Select'"
    class="form-control cursor-pointer [&_select]:cursor-pointer !min-w-36 max-w-36"
    type="select"
    :model-value="props.value || undefined"
    :options="filter.options"
    :placeholder="filter.label"
    @update:modelValue="(v) => updateFilter(filter, v || '')"
  />
  <Link
    v-else-if="filter.type === 'Link'"
    :model-value="props.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    :title="
      props.value ? linkTitle?.(props.value) || String(props.value) : undefined
    "
    class="!min-w-36 max-w-36 [&_input]:truncate"
    @update:model-value="(value) => updateFilter(filter, value ?? '')"
  />
  <component
    v-else-if="['Date', 'Datetime'].includes(filter.type)"
    class="border-none !min-w-36 max-w-36 [&_input]:truncate"
    :is="filter.type === 'Date' ? DatePicker : DateTimePicker"
    :model-value="props.value"
    @change="(v) => updateFilter(filter, v)"
    :placeholder="filter.label"
  />
  <TextInput
    v-else
    :value="props.value"
    type="text"
    :placeholder="filter.label"
    @input.stop="debouncedFn(filter, $event.target.value)"
    class="border-none !min-w-36 max-w-36 [&_input]:truncate"
  />
</template>
<script setup>
import { Link } from "@framework/ui";
import { useDebounceFn } from "@vueuse/core";
import { DatePicker, DateTimePicker, FormControl, TextInput } from "frappe-ui";

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
  value: {
    type: [String, Boolean],
    required: true,
  },
  // what the Link shows for its value until its search loads; the ID if not given
  linkTitle: Function,
});

const emit = defineEmits(["applyQuickFilter"]);

const debouncedFn = useDebounceFn((f, value) => {
  emit("applyQuickFilter", f, value);
}, 500);

function updateFilter(f, value) {
  emit("applyQuickFilter", f, value);
}
</script>
