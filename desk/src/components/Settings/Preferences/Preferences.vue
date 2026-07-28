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
          <div class="mt-6">
            <LanguageTimezoneSetting :user="user" />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { Button, createDocumentResource, toast } from "frappe-ui";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import UnsavedBadge from "@/components/UnsavedBadge.vue";
import HDLogo from "@/assets/logos/HDLogo.vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";
import { useConfigStore } from "@/stores/config";
import { disableSettingModalOutsideClick } from "../settingsModal";
import ThemeSwitcher from "./components/ThemeSwitcher.vue";
import LanguageTimezoneSetting from "./components/LanguageTimezoneSetting.vue";

const config = useConfigStore();
const { userId } = useAuthStore();
const user = createDocumentResource({ doctype: "User", name: userId });

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
