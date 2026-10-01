<template>
  <SettingsLayoutBase
    :title="__('Knowledge Base')"
    :description="__('Manage how the knowledge base appears to customers.')"
  >
    <template #content>
      <div class="flex flex-col">
        <LogoUpload
          :title="__('Banner image')"
          :description="
            __(
              'Appears behind the search bar on the customer portal. Recommended size is minimum 1440x240 px in PNG or JPG.'
            )
          "
          :image="settings.doc?.banner_image || ''"
          :is-loading="settings.setValue.loading"
          @onUpload="(url) => update('banner_image', url)"
          @onRemove="showRemoveDialog = true"
        />
        <div class="flex flex-col gap-6 mt-8">
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">{{
                __("Public knowledge base")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __("Anyone can read articles without signing in.")
              }}</span>
            </div>
            <Switch
              :model-value="Boolean(settings.doc?.public_knowledge_base)"
              @update:model-value="
                (value) => update('public_knowledge_base', value)
              "
            />
          </div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">{{
                __("Prefer knowledge base")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __("Guide users to articles before tickets.")
              }}</span>
            </div>
            <Switch
              :model-value="Boolean(settings.doc?.prefer_knowledge_base)"
              @update:model-value="
                (value) => update('prefer_knowledge_base', value)
              "
            />
          </div>
          <div class="flex items-center justify-between">
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">{{
                __("Anonymous voting on articles")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __("Allow anonymous users to vote on articles.")
              }}</span>
            </div>
            <Switch
              :model-value="
                Boolean(settings.doc?.allow_anonymous_article_voting)
              "
              @update:model-value="
                (value) => update('allow_anonymous_article_voting', value)
              "
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="showRemoveDialog"
    :title="__('Remove banner image')"
    :message="__('Are you sure you want to remove the banner image?')"
    :onConfirm="removeBanner"
    :onCancel="() => (showRemoveDialog = false)"
  />
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { useConfigStore } from "@/stores/config";
import { __ } from "@/translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";
import { ref } from "vue";
import LogoUpload from "../General/components/LogoUpload.vue";

const configStore = useConfigStore();
const settings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});
const showRemoveDialog = ref(false);

// Every control here writes a single field, so each edit saves itself — the tab
// never carries a dirty state and needs no Save button.
function update(fieldname: string, value: string | boolean) {
  settings.setValue.submit({ [fieldname]: value }, { onSuccess: onSaved });
}

function onSaved() {
  // Both fields are served to the portals through `get_config`.
  configStore.configResource.reload();
  toast.success(__("Settings updated"));
}

function removeBanner() {
  showRemoveDialog.value = false;
  update("banner_image", "");
}
</script>
