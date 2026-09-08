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
              Boolean(settings.doc?.allow_customer_managers_to_invite)
            "
            @update:model-value="
              (value) => update('allow_customer_managers_to_invite', value)
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
                "Customer managers can change their own organization's logo. Renaming stays with agents."
              )
            }}</span>
          </div>
          <Switch
            :model-value="
              Boolean(
                settings.doc?.allow_customer_managers_to_edit_organization
              )
            "
            @update:model-value="
              (value) =>
                update('allow_customer_managers_to_edit_organization', value)
            "
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
// What customer managers may do from the customer portal, in one place.
//
// The switches default off: most helpdesks keep user administration agent-side,
// and turning the first one on lets a customer create logins for your helpdesk. They only
// decide whether the portal draws the controls — the server enforces them independently,
// in `helpdesk/api/organization.py` and the `User Invitation` before_insert hook.
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { useConfigStore } from "@/stores/config";
import { __ } from "@/translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";

const configStore = useConfigStore();
const settings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

// Each switch saves itself, so the tab never carries a dirty state — same as the
// Knowledge Base tab it sits beside.
function update(fieldname: string, value: boolean) {
  settings.setValue.submit({ [fieldname]: value }, { onSuccess: onSaved });
}

function onSaved() {
  // The portal reads both through `get_config`, so refresh what it will be handed.
  configStore.configResource.reload();
  toast.success(__("Settings updated"));
}
</script>
