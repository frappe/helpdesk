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
                  {{ __("Show exact timestamps") }}
                </span>
                <span class="text-p-sm text-ink-gray-6">
                  {{
                    __(
                      "Show the exact date & time in the activity timeline instead of relative time."
                    )
                  }}
                </span>
              </div>
              <Switch
                :model-value="showExactTimestamp"
                @update:model-value="setShowExactTimestamp"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { Button, Switch, createDocumentResource, toast } from "frappe-ui";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { disableSettingModalOutsideClick } from "../settingsModal";
import ThemeSwitcher from "./components/ThemeSwitcher.vue";
import LanguageTimezoneSetting from "./components/LanguageTimezoneSetting.vue";

const TIMESTAMP_FIELD = "show_absolute_datetime_in_timeline";

const config = useConfigStore();
const { userId, reloadUser } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

const showExactTimestamp = computed(() => !!user.doc?.[TIMESTAMP_FIELD]);
function setShowExactTimestamp(value: boolean) {
  user.doc[TIMESTAMP_FIELD] = value ? 1 : 0;
}

const isDirty = computed(() => {
  if (!user.originalDoc) return false;
  return (
    user.doc?.language !== user.originalDoc?.language ||
    user.doc?.time_zone !== user.originalDoc?.time_zone ||
    user.doc?.[TIMESTAMP_FIELD] !== user.originalDoc?.[TIMESTAMP_FIELD]
  );
});

function save() {
  // Language/timezone changes take effect app-wide only after a reload; the
  // timestamp preference just needs the auth store refreshed.
  const needsReload =
    user.doc?.language !== user.originalDoc?.language ||
    user.doc?.time_zone !== user.originalDoc?.time_zone;

  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__("Preferences updated successfully."));
      if (needsReload) {
        window.location.reload();
        return;
      }
      reloadUser();
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
