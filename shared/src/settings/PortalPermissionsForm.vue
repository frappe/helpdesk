<template>
  <!-- Wait for settings: early off switches would look saved. -->
  <Transition
    enter-from-class="opacity-0"
    enter-active-class="transition-opacity duration-200 motion-reduce:transition-none"
  >
    <div v-if="ready" class="space-y-11">
      <section v-for="section in sections" :key="section.title">
        <h2 class="text-md-semibold text-ink-gray-8">{{ section.title }}</h2>
        <div class="mt-2 divide-y divide-outline-gray-1">
          <SettingsRow
            v-for="toggle in section.toggles"
            :key="toggle.fieldname"
            :title="toggle.label"
            :description="toggle.description"
          >
            <Switch
              :model-value="
                Boolean(toggle.settings.doc?.[toggle.fieldname]) !==
                Boolean(toggle.inverted)
              "
              @update:model-value="
                (value) => save(toggle, value !== Boolean(toggle.inverted))
              "
            />
          </SettingsRow>
        </div>
      </section>
    </div>
    <SettingsFormSkeleton
      v-else
      :sections="
        sections.map((section) => ({
          title: section.title,
          rows: section.toggles.length,
        }))
      "
    />
  </Transition>
</template>

<script setup lang="ts">
import { __ } from "../translation";
import {
  createDocumentResource,
  createResource,
  getCachedDocumentResource,
  SettingsRow,
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
const sections = computed(() => [
  {
    title: __("Access"),
    toggles: [
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
        fieldname: "allow_anyone_to_create_tickets",
        label: __("Allow anyone to create tickets"),
        description: __(
          "Visitors will be able to raise tickets from the portal without logging in."
        ),
      },
      // Shown as "Allow": the field stores the opposite. Counted while
      // unknown, so the skeleton has a row for it.
      ...(!canEditSignup.fetched || canEditSignup.data?.has_permission
        ? [
            {
              settings: websiteSettings,
              fieldname: "disable_signup",
              inverted: true,
              label: __("Allow signup"),
              description: __(
                "Anyone can create a portal account. When off, system managers register new users."
              ),
            },
          ]
        : []),
    ],
  },
  {
    title: __("Customer managers"),
    toggles: [
      {
        settings: hdSettings,
        fieldname: "allow_customer_managers_to_invite",
        label: __("Allow member invites"),
        description: __(
          "Invite people to their organization. Invited people get a portal login."
        ),
      },
      {
        settings: hdSettings,
        fieldname: "allow_customer_managers_to_manage_members",
        label: __("Allow member management"),
        description: __("Change member roles and remove members."),
      },
      {
        settings: hdSettings,
        fieldname: "allow_customer_managers_to_edit_organization",
        label: __("Allow organization edits"),
        description: __("Change their organization's logo."),
      },
    ],
  },
]);

function save(toggle, value: boolean) {
  toggle.settings.setValue.submit(
    { [toggle.fieldname]: value },
    { onSuccess: () => toast.success(__("Settings updated")) }
  );
}
</script>
