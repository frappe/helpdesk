<template>
  <WhatsAppTemplatePage
    v-if="page === 'template'"
    :key="record || 'new'"
    :name="record"
    :default-account="settings.doc?.default_account"
    @back="page = 'tabs'"
  />
  <WhatsAppAccountPage
    v-else-if="page === 'account'"
    :key="record || 'new'"
    :name="record"
    @back="page = 'tabs'"
  />
  <SettingsLayoutBase
    v-else
    :title="__('WhatsApp')"
    :description="
      __('Receive and reply to customer WhatsApp messages as tickets.')
    "
  >
    <template #header-actions>
      <Button
        v-if="tab === 'templates'"
        :label="__('New template')"
        theme="gray"
        variant="solid"
        icon-left="lucide-plus"
        @click="open('template', '')"
      />
      <Button
        v-else-if="tab === 'accounts'"
        :label="__('New account')"
        theme="gray"
        variant="solid"
        icon-left="lucide-plus"
        @click="open('account', '')"
      />
      <Button
        v-else-if="webhook?.isDirty"
        :label="__('Save')"
        theme="gray"
        variant="solid"
        :loading="webhook.saving"
        @click="webhook.save()"
      />
    </template>
    <template #content>
      <Tabs
        v-model="activeTab"
        :tabs="tabs"
        class="flex-1 [&_[role='tablist']]:px-0 [&_[role='tabpanel'][data-state='inactive']]:hidden"
      >
        <template #tab-panel="{ tab: panel }">
          <div class="pt-5">
            <WhatsAppTemplates
              v-if="panel.value === 'templates'"
              @open="(name) => open('template', name)"
            />
            <WhatsAppAccounts
              v-else-if="panel.value === 'accounts'"
              :settings="settings"
              @open="(name) => open('account', name)"
            />
            <WhatsAppWebhook v-else ref="webhook" :settings="settings" />
          </div>
        </template>
      </Tabs>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { Button, createDocumentResource, Tabs, toast } from "frappe-ui";
import { computed, ref, useTemplateRef } from "vue";
import WhatsAppAccountPage from "./WhatsAppAccountPage.vue";
import WhatsAppAccounts from "./WhatsAppAccounts.vue";
import WhatsAppTemplatePage from "./WhatsAppTemplatePage.vue";
import WhatsAppTemplates from "./WhatsAppTemplates.vue";
import WhatsAppWebhook from "./WhatsAppWebhook.vue";

type Tab = "templates" | "accounts" | "advanced";

// Templates first: they change far more often than the accounts or the webhook
const tabs = [
  { value: "templates", label: __("Templates") },
  { value: "accounts", label: __("Accounts") },
  { value: "advanced", label: __("Advanced") },
];

const page = ref<"tabs" | "template" | "account">("tabs");
// "" opens a new record
const record = ref("");
const tab = ref<Tab>("templates");
const webhook = useTemplateRef("webhook");

// One copy for both tabs, so setting the default account never goes stale in the webhook form
const settings = createDocumentResource({
  doctype: "WA Settings",
  name: "WA Settings",
  auto: true,
  setValue: {
    onError: (error: { messages?: string[] }) =>
      toast.error(error?.messages?.[0] || __("Something went wrong")),
  },
});

// Unsaved webhook edits ask before the tab changes
const activeTab = computed({
  get: () => tab.value,
  set: (value: Tab) => {
    if (tab.value === "advanced" && webhook.value) {
      webhook.value.leave(() => (tab.value = value));
    } else {
      tab.value = value;
    }
  },
});

function open(kind: "template" | "account", name: string) {
  record.value = name;
  page.value = kind;
}
</script>
