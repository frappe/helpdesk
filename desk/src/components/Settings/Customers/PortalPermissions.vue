<template>
  <SettingsLayoutBase
    :title="__('Portal permissions')"
    :description="
      __(
        'Choose what visitors and customer managers can do from the customer portal.'
      )
    "
  >
    <template #content>
      <div class="flex flex-col gap-6">
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
            :model-value="Boolean(hdSettings.doc?.[toggle.fieldname])"
            @update:model-value="(value) => save(toggle.fieldname, value)"
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
import { computed } from "vue";

// computed, so labels follow a translation load
const toggles = computed(() => [
  {
    fieldname: "allow_anyone_to_create_tickets",
    label: __("Allow anyone to create tickets"),
    description: __(
      "Visitors can raise a ticket from the portal without signing in. If their email already has an account, they're asked to sign in instead."
    ),
  },
  {
    fieldname: "allow_customer_managers_to_invite",
    label: __("Invite and manage members"),
    description: __(
      "Customer managers can invite people into their own organization, change their roles and remove them. Invited people get a login for your helpdesk."
    ),
  },
  {
    fieldname: "allow_customer_managers_to_edit_organization",
    label: __("Edit organization details"),
    description: __(
      "Customer managers can change their own organization's name and logo."
    ),
  },
]);

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

function save(fieldname: string, value: boolean) {
  hdSettings.setValue.submit(
    { [fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
