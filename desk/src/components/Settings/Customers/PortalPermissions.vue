<template>
  <SettingsLayoutBase
    :title="__('Portal permissions')"
    :description="
      __('Choose what customer managers can do from the customer portal.')
    "
  >
    <template #content>
      <div class="flex flex-col gap-6">
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">{{
              __("Invite and manage members")
            }}</span>
            <span class="text-p-sm text-ink-gray-6">{{
              __(
                "Customer managers can invite people into their own organization, change their roles and remove them. Invited people get a login for your helpdesk."
              )
            }}</span>
          </div>
          <Switch
            :model-value="
              Boolean(hdSettings.doc?.allow_customer_managers_to_invite)
            "
            @update:model-value="
              (value) => onToggle('allow_customer_managers_to_invite', value)
            "
          />
        </div>
        <div class="flex items-center justify-between">
          <div class="flex flex-col gap-1">
            <span class="text-base-medium text-ink-gray-8">{{
              __("Edit organization details")
            }}</span>
            <span class="text-p-sm text-ink-gray-6">{{
              __(
                "Customer managers can change their own organization's name and logo."
              )
            }}</span>
          </div>
          <Switch
            :model-value="
              Boolean(
                hdSettings.doc?.allow_customer_managers_to_edit_organization
              )
            "
            @update:model-value="
              (value) =>
                onToggle('allow_customer_managers_to_edit_organization', value)
            "
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

function onToggle(fieldname: string, value: boolean) {
  hdSettings.setValue.submit(
    { [fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
