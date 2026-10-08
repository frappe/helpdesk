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
    label: __("Allow member invites"),
    description: __(
      "Customer managers will be able to invite people to their organization. Invited people get a portal login."
    ),
  },
  {
    settings: hdSettings,
    fieldname: "allow_customer_managers_to_change_roles",
    label: __("Allow role changes"),
    description: __(
      "Customer managers will be able to promote members to managers, or demote them back."
    ),
  },
  {
    settings: hdSettings,
    fieldname: "allow_customer_managers_to_remove_members",
    label: __("Allow member removal"),
    description: __(
      "Customer managers will be able to remove people from their organization."
    ),
  },
  {
    settings: hdSettings,
    fieldname: "allow_customer_managers_to_edit_organization",
    label: __("Allow organization edits"),
    description: __(
      "Customer managers will be able to change their organization's logo."
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
