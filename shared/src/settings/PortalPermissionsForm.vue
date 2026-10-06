<template>
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
        :model-value="Boolean(toggle.settings.doc?.[toggle.fieldname])"
        @update:model-value="(value) => save(toggle, value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import { createDocumentResource, Switch, toast } from "frappe-ui";
import { computed } from "vue";

const hdSettings = createDocumentResource({
  doctype: "HD Settings",
  name: "HD Settings",
});

const websiteSettings = createDocumentResource({
  doctype: "Website Settings",
  name: "Website Settings",
});

// computed, so labels follow a translation load
const toggles = computed(() => [
  {
    settings: websiteSettings,
    fieldname: "disable_signup",
    label: __("Disable signup"),
    description: __(
      "New users will have to be manually registered by system managers."
    ),
  },
  {
    settings: hdSettings,
    fieldname: "allow_customer_managers_to_invite",
    label: __("Invite and manage members"),
    description: __(
      "Customer managers can invite people into their own organization, change their roles and remove them. Invited people get a login for your helpdesk."
    ),
  },
  {
    settings: hdSettings,
    fieldname: "allow_customer_managers_to_edit_organization",
    label: __("Edit organization details"),
    description: __(
      "Customer managers can change their own organization's name and logo."
    ),
  },
]);

function save(toggle, value: boolean) {
  toggle.settings.setValue.submit(
    { [toggle.fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
