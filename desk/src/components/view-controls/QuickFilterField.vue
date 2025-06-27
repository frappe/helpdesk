<template>
  <FormControl
    v-if="filter.type == 'Check'"
    :label="filter.label"
    type="checkbox"
    v-model="filter.value"
    @change.stop="updateFilter(filter, $event.target.checked)"
    class="w-44"
  />
  <FormControl
    v-else-if="filter.type === 'Select'"
    class="form-control cursor-pointer [&_select]:cursor-pointer w-44"
    type="select"
    v-model="filter.value"
    :options="filter.options"
    :placeholder="filter.label"
    @change.stop="updateFilter(filter, $event.target.value)"
  />
  <Link
    v-else-if="filter.type === 'Link'"
    :value="filter.value"
    :doctype="filter.options"
    :placeholder="filter.label"
    @change="(data) => updateFilter(filter, data)"
    class="w-44"
  />
  <component
    v-else-if="['Date', 'Datetime'].includes(filter.type)"
    class="border-none w-44"
    :is="filter.type === 'Date' ? DatePicker : DateTimePicker"
    :value="filter.value"
    @change="(v) => updateFilter(filter, v)"
    :placeholder="filter.label"
  />
  <TextInput
    v-else
    v-model="filter.value"
    type="text"
    :placeholder="filter.label"
    @input.stop="debouncedFn(filter, $event.target.value)"
  />
</template>
<script setup>
import { Link } from "@/components";
import { useDebounceFn } from "@vueuse/core";
import { DatePicker, DateTimePicker, FormControl, TextInput } from "frappe-ui";

const props = defineProps({
  filter: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["applyQuickFilter"]);

const debouncedFn = useDebounceFn((f, value) => {
  emit("applyQuickFilter", f, value);
}, 500);

function updateFilter(f, value) {
  emit("applyQuickFilter", f, value);
}
</script>
