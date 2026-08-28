<template>
  <SettingsLayoutBase :description="__('Manage your personal preferences.')">
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg-semibold text-ink-gray-8">
          {{ __("Preferences") }}
        </h1>
        <UnsavedBadge :show="isDirty" />
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <Button
          v-if="isDirty"
          variant="solid"
          :label="__('Save')"
          :loading="user.save.loading"
          @click="save"
        />
      </Transition>
    </template>
    <template #content>
      <div class="flex flex-col">
        <div>
          <div class="text-base-semibold text-ink-gray-9">
            {{ __("Appearance") }}
          </div>
          <ThemeSwitcher
            :name="config.brandName || 'Helpdesk'"
            :logo="config.brandLogo || HDLogo"
          />
        </div>
        <hr class="my-8" />
        <div>
          <div class="text-base-semibold text-ink-gray-9">
            {{ __("Language & Time") }}
          </div>
          <div class="mt-6 flex flex-col gap-6">
            <LanguageTimezoneSetting :user="user" />
            <div class="flex items-center justify-between gap-4">
              <div class="flex flex-col gap-1">
                <span class="text-base-medium text-ink-gray-8">
                  {{ __("Timeline timestamp format") }}
                </span>
                <span class="text-p-sm text-ink-gray-6">
                  {{
                    __(
                      "Show timestamps in the activity timeline as relative time (5 mins ago) or an exact date & time."
                    )
                  }}
                </span>
              </div>
              <!-- select-type FormControl forces w-full, so the wrapper caps it -->
              <div class="w-40 shrink-0">
                <FormControl
                  v-model="timestampFormat"
                  type="select"
                  :options="timestampFormatOptions"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { Button, FormControl, createDocumentResource, toast } from "frappe-ui";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { useTimelinePreferences } from "@/composables/timelinePreferences";
import { disableSettingModalOutsideClick } from "../settingsModal";
import ThemeSwitcher from "./components/ThemeSwitcher.vue";
import LanguageTimezoneSetting from "./components/LanguageTimezoneSetting.vue";

const config = useConfigStore();
const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

// stored per user in localStorage, applies instantly — no Save needed
const { timestampFormat } = useTimelinePreferences();
const timestampFormatOptions = [
  { label: __("Relative"), value: "Relative" },
  { label: __("Exact"), value: "Exact" },
];

const isDirty = computed(() => {
  if (!user.originalDoc) return false;
  return (
    user.doc?.language !== user.originalDoc?.language ||
    user.doc?.time_zone !== user.originalDoc?.time_zone
  );
});

function save() {
  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__("Preferences updated successfully."));
      // Language/timezone changes require a reload to take effect app-wide.
      window.location.reload();
    },
    onError: (error: { message: string; messages: string[] }) => {
      toast.error(error.message + ": " + error.messages?.[0]);
    },
  });
}

watch(isDirty, (value) => {
  disableSettingModalOutsideClick.value = value;
});
</script>
