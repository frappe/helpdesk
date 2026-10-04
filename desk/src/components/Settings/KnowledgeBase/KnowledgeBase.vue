<template>
  <SettingsLayoutBase
    :title="__('Knowledge Base')"
    :description="__('Manage how the knowledge base appears to customers.')"
  >
    <template #content>
      <div class="flex flex-col">
        <BannerPicker
          :image="settings.doc?.banner_image || ''"
          :preset="settings.doc?.banner_preset || ''"
          @change="save"
        />
        <div class="mt-8 flex flex-col gap-6">
          <div
            v-for="toggle in toggles"
            :key="toggle.fieldname"
            class="flex items-center justify-between"
          >
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">
                {{ toggle.label }}
              </span>
              <span class="text-p-sm text-ink-gray-6">
                {{ toggle.description }}
              </span>
            </div>
            <Switch
              :model-value="Boolean(settings.doc?.[toggle.fieldname])"
              @update:model-value="
                (value) => save({ [toggle.fieldname]: value })
              "
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";
import { computed } from "vue";
import BannerPicker from "./BannerPicker.vue";

// computed, so labels follow a translation load
const toggles = computed(() => [
  {
    fieldname: "public_knowledge_base",
    label: __("Public knowledge base"),
    description: __("Anyone can read articles without signing in."),
  },
  {
    fieldname: "allow_anonymous_article_voting",
    label: __("Anonymous voting on articles"),
    description: __("Allow anonymous users to vote on articles."),
  },
]);

const settings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

function save(values: Record<string, string | boolean>) {
  settings.setValue.submit(values, {
    onSuccess: () => toast.success(__("Settings updated")),
  });
}
</script>
