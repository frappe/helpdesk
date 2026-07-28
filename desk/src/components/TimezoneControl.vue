<template>
  <Autocomplete
    :label="label ? __(label) : undefined"
    :options="options"
    :placeholder="__('Select timezone')"
    :loading="timezoneResource.loading"
    :model-value="modelValue"
    @update:model-value="(v: { label: string; value: string } | string) => (modelValue = typeof v === 'string' ? v : v.value)"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Autocomplete, createResource } from "frappe-ui";
import { computed } from "vue";

const props = defineProps<{
  label?: string;
}>();

const modelValue = defineModel<string>({ default: "" });

const timezoneResource = createResource({
  url: "frappe.core.doctype.user.user.get_timezones",
  auto: true,
  cache: ["Timezones"],
});

const options = computed<string[]>(
  () => timezoneResource.data?.timezones ?? []
);
</script>
