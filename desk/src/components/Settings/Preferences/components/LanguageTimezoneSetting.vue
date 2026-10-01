<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between gap-4">
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">
          {{ __("Language") }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ __("Change language of the application.") }}
        </span>
      </div>
      <Link
        :model-value="user.doc?.language"
        doctype="Language"
        class="w-40"
        @update:model-value="updateLanguage"
      />
    </div>
    <div class="flex items-center justify-between gap-4">
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">
          {{ __("Timezone") }}
        </span>
        <span class="text-p-sm text-ink-gray-6">
          {{ __("Change timezone of the application.") }}
        </span>
      </div>
      <Autocomplete
        :model-value="user.doc?.time_zone"
        :options="timezoneOptions"
        :placeholder="__('Select Timezone')"
        size="sm"
        class="w-40"
        @update:model-value="updateTimezone"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { createResource } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps<{ user: any }>();

function updateLanguage(value: string | null) {
  if (!props.user.doc) return;
  props.user.doc.language = value || props.user.originalDoc?.language;
}

function updateTimezone(value: { label: string; value: string } | null) {
  if (!props.user.doc) return;
  props.user.doc.time_zone = value?.value || props.user.originalDoc?.time_zone;
}

const timezoneOptions = ref<{ label: string; value: string }[]>([]);
createResource({
  url: "frappe.core.doctype.user.user.get_timezones",
  auto: true,
  onSuccess(data: { timezones: string[] }) {
    timezoneOptions.value = data.timezones.map((tz) => ({
      label: tz,
      value: tz,
    }));
  },
});
</script>
