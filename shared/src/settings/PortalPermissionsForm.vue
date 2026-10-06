<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">{{
          __("Disable signup")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">{{
          __(
            "New users will have to be manually registered by system managers."
          )
        }}</span>
      </div>
      <Switch
        :model-value="Boolean(websiteSettings.doc?.disable_signup)"
        @update:model-value="
          (value) =>
            websiteSettings.setValue.submit(
              { disable_signup: value },
              { onSuccess: () => toast.success(__('Settings updated')) }
            )
        "
      />
    </div>
    <div class="flex items-center justify-between">
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">{{
          __("Invite members")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">{{
          __(
            "Customer managers can invite people into their own organization. Invited people get a login for your helpdesk."
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
          __("Change member roles")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">{{
          __(
            "Customer managers can make members of their own organization managers, and back."
          )
        }}</span>
      </div>
      <Switch
        :model-value="
          Boolean(hdSettings.doc?.allow_customer_managers_to_change_roles)
        "
        @update:model-value="
          (value) => onToggle('allow_customer_managers_to_change_roles', value)
        "
      />
    </div>
    <div class="flex items-center justify-between">
      <div class="flex flex-col gap-1">
        <span class="text-base-medium text-ink-gray-8">{{
          __("Remove members")
        }}</span>
        <span class="text-p-sm text-ink-gray-6">{{
          __("Customer managers can remove people from their own organization.")
        }}</span>
      </div>
      <Switch
        :model-value="
          Boolean(hdSettings.doc?.allow_customer_managers_to_remove_members)
        "
        @update:model-value="
          (value) =>
            onToggle('allow_customer_managers_to_remove_members', value)
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
          Boolean(hdSettings.doc?.allow_customer_managers_to_edit_organization)
        "
        @update:model-value="
          (value) =>
            onToggle('allow_customer_managers_to_edit_organization', value)
        "
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

const websiteSettings = createDocumentResource({
  doctype: "Website Settings",
  name: "Website Settings",
});

function onToggle(fieldname: string, value: boolean) {
  hdSettings.setValue.submit(
    { [fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
