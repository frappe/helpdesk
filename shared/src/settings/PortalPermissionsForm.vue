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
          <!-- label-for="": a title click must not flip the switch, so aria-label names it -->
          <SettingsRow
            label-for=""
            v-for="toggle in section.toggles"
            :key="toggle.fieldname"
            :title="toggle.label"
            :description="toggle.description"
          >
            <Switch
              :aria-label="toggle.label"
              :model-value="
                Boolean(toggle.settings.doc?.[toggle.fieldname]) !==
                Boolean(toggle.inverted)
              "
              :disabled="toggle.disabled"
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
        label: __("Use knowledge base as customer home"),
        description: __(
          "Customers will land on the knowledge base when they log in, instead of their tickets."
        ),
      },
      {
        settings: hdSettings,
        fieldname: "knowledge_base_home_page_for_guests",
        label: __("Set knowledge base as guest home"),
        description: __(
          "Guests land on the knowledge base landing page instead of the login page."
        ),
        // Guests only reach a public knowledge base. Left on, it can still be turned off.
        disabled:
          !hdSettings.doc?.public_knowledge_base &&
          !hdSettings.doc?.knowledge_base_home_page_for_guests,
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
        fieldname: "allow_customer_managers_to_manage_organization",
        label: __("Allow organization management"),
        description: __(
          "Change member roles, remove members and change the organization's logo."
        ),
      },
      {
        settings: hdSettings,
        fieldname: "allow_customer_managers_to_invite",
        label: __("Allow member invites"),
        description: __(
          "Invite people to their organization. Invited people get a portal login."
        ),
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
