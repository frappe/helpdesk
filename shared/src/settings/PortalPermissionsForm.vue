<template>
  <!-- Wait for settings: early off switches would look saved. -->
  <Transition
    enter-from-class="opacity-0"
    enter-active-class="transition-opacity duration-200 motion-reduce:transition-none"
  >
    <div v-if="ready" class="flex flex-col gap-6">
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
    <SettingsFormSkeleton v-else :toggles="4" />
  </Transition>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import {
  createDocumentResource,
  createResource,
  getCachedDocumentResource,
  Switch,
  toast,
} from "frappe-ui";
import { computed } from "vue";
import SettingsFormSkeleton from "./SettingsFormSkeleton.vue";

// The portal mounts all panels at once; re-creating a cached doc refetches.
const hdSettings =
  getCachedDocumentResource("HD Settings", "HD Settings") ||
  createDocumentResource({ doctype: "HD Settings", name: "HD Settings" });

const websiteSettings = createDocumentResource({
  doctype: "Website Settings",
  name: "Website Settings",
});

// Only admins can write Website Settings; others would hit PermissionError.
const canEditSignup = createResource({
  url: "frappe.client.has_permission",
  params: {
    doctype: "Website Settings",
    docname: "Website Settings",
    perm_type: "write",
  },
  auto: true,
});

const ready = computed(
  () =>
    Boolean(hdSettings.doc) &&
    canEditSignup.fetched &&
    (!canEditSignup.data?.has_permission || Boolean(websiteSettings.doc))
);

// computed, so labels follow a translation load
const toggles = computed(() => [
  {
    settings: hdSettings,
    fieldname: "prefer_knowledge_base",
    label: __("Use knowledge base as home"),
    description: __(
      "Customers will land on the knowledge base when they log in or open the site, instead of their tickets."
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
    fieldname: "allow_customer_managers_to_manage_members",
    label: __("Allow member management"),
    description: __(
      "Customer managers will be able to change member roles and remove members."
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
  ...(canEditSignup.data?.has_permission
    ? [
        {
          settings: websiteSettings,
          fieldname: "disable_signup",
          label: __("Disable signup"),
          description: __(
            "New users will have to be manually registered by system managers."
          ),
        },
      ]
    : []),
]);

function save(toggle, value: boolean) {
  toggle.settings.setValue.submit(
    { [toggle.fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
