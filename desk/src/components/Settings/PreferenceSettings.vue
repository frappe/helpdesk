<template>
  <SettingsLayoutBase
    v-if="user.doc"
    :title="__('Preferences')"
    :description="
      __(
        'Choose how you want to use the application by setting your preferences.'
      )
    "
  >
    <template #content>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center h-7">
            <div class="text-base font-semibold text-gray-900">
              {{ __("Language & Time") }}
            </div>
            <Badge
              v-if="isDirty"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
          <Button
            v-if="isDirty"
            :label="__('Save')"
            :loading="user.save.loading"
            @click="save()"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Language") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Change language of the application.") }}
            </span>
          </div>
          <Link
            v-model="user.doc.language"
            @update:modelValue="user.doc.language = $event || language"
            doctype="Language"
            class="w-40"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __("Timezone") }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __("Change timezone of the application.") }}
            </span>
          </div>
          <Autocomplete
            :model-value="user.doc.time_zone"
            @update:modelValue="user.doc.time_zone = $event?.value"
            class="w-40"
            :options="timezoneOptions"
            size="sm"
            placeholder="Select Timezone"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import {
  Combobox,
  Badge,
  toast,
  createResource,
  createDocumentResource,
} from "frappe-ui";
import Link from "../frappe-ui/Link.vue";
import { useAuthStore } from "@/stores/auth";

import { ref, computed } from "vue";
import Autocomplete from "../Autocomplete.vue";

const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

const timezoneOptions = ref([]);
const timezoneData = createResource({
  url: "frappe.core.doctype.user.user.get_timezones",
  auto: true,
  onSuccess(data) {
    timezoneOptions.value = data.timezones.map((tz) => ({
      label: tz,
      value: tz,
    }));
  },
});

const language = ref(user.doc.language);
const refreshRequired = ref(false);

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc);
});

function save() {
  refreshRequired.value =
    user.doc.language !== user.originalDoc?.language ||
    user.doc.time_zone !== user.originalDoc?.time_zone;

  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__("Preferences Updated Successfully"));
      if (refreshRequired.value) {
        window.location.reload();
      }
    },
    onError: (err) => {
      toast.error(err.message + ": " + err.messages[0]);
    },
  });
}
</script>
