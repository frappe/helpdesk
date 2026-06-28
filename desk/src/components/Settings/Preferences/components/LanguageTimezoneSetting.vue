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
        :placeholder="__('Select Language')"
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
      <TimezoneControl
        :model-value="user.doc?.time_zone"
        class="w-40"
        @update:model-value="updateTimezone"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import TimezoneControl from "@/components/TimezoneControl.vue";
import { __ } from "@/translation";
import { Link } from "frappe-ui/frappe";

const props = defineProps<{ user: any }>();

function updateLanguage(value: string | null) {
  if (!props.user.doc) return;
  props.user.doc.language = value || props.user.originalDoc?.language;
}

function updateTimezone(value: string | null) {
  if (!props.user.doc) return;
  props.user.doc.time_zone = value || props.user.originalDoc?.time_zone;
}
</script>
