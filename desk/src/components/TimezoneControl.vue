<template>
  <Combobox
    v-model="modelValue"
    trigger="button"
    :label="label ? __(label) : undefined"
    :options="options"
    :placeholder="__('Select timezone')"
    :loading="timezoneResource.loading"
  />
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Combobox, createResource } from "frappe-ui";
import { computed } from "vue";

defineProps<{
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
