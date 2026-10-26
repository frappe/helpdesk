<template>
  <SettingsLayoutBase
    :title="__('WhatsApp')"
    :description="
      __('Receive and reply to customer WhatsApp messages as tickets.')
    "
  >
    <template
      v-if="accounts.data?.length || accounts.list.error"
      #header-actions
    >
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        icon-left="lucide-plus"
        @click="open('')"
      />
    </template>
    <template #content>
      <div class="flex flex-col gap-8">
        <section class="flex flex-col gap-3">
          <h2 class="text-base-medium text-ink-gray-8">
            {{ __("Webhook") }}
          </h2>
          <p class="text-p-sm text-ink-gray-6">
            {{
              __(
                "In your Meta app, open WhatsApp > Configuration, paste the Callback URL and the Verify token below, then subscribe to the messages and message_template_status_update fields."
              )
            }}
          </p>
          <div class="flex items-end gap-2">
            <TextInput
              class="min-w-0 flex-1"
              :label="__('Callback URL')"
              :model-value="webhookUrl"
              readonly
              data-testid="whatsapp-webhook-url"
            />
            <Button
              icon="lucide-copy"
              :tooltip="__('Copy')"
              :aria-label="__('Copy webhook URL')"
              @click="copyToClipboard(webhookUrl)"
            />
          </div>
          <template v-if="settings.doc">
            <Alert
              v-if="!settings.originalDoc?.webhook_secret"
              theme="amber"
              :title="
                __(
                  'Without the App secret, anyone who knows the Callback URL can send fake messages.'
                )
              "
              data-testid="whatsapp-secret-warning"
            />
            <div class="grid gap-3 sm:grid-cols-2">
              <TextInput
                v-model="settings.doc.webhook_verify_token"
                :label="__('Verify token')"
                :placeholder="__('Any text you choose')"
              />
              <Password
                v-model="settings.doc.webhook_secret"
                :label="__('App secret')"
                :description="__('Meta app > App settings > Basic')"
              />
            </div>
            <div v-if="settings.isDirty">
              <Button
                :label="__('Save')"
                variant="solid"
                :loading="settings.save.loading"
                @click="saveWebhook"
              />
            </div>
          </template>
        </section>

        <section class="flex flex-col gap-2">
          <h2 class="text-base-medium text-ink-gray-8">
            {{ __("Accounts") }}
          </h2>
          <div
            v-if="!accounts.data && !accounts.list.error"
            class="flex items-center justify-center py-10 text-ink-gray-5"
          >
            <LoadingIndicator class="size-4" />
          </div>
          <Alert
            v-else-if="accounts.list.error"
            theme="red"
            :title="__('Could not load accounts')"
            :primary-action="{ label: __('Retry'), onClick: accounts.reload }"
            data-testid="whatsapp-accounts-error"
          />
          <div v-else-if="accounts.data.length" class="-mx-2 flex flex-col">
            <template
              v-for="(account, index) in accounts.data"
              :key="account.name"
            >
              <hr v-if="index" class="mx-2 border-outline-elevation-2" />
              <div
                class="flex items-center gap-3 rounded-4 px-2 py-3 hover:bg-surface-gray-2"
                data-testid="whatsapp-account"
              >
                <button
                  class="flex min-w-0 flex-1 flex-col items-start gap-1 text-start"
                  @click="open(account.name)"
                >
                  <span class="flex max-w-full items-center gap-1.5">
                    <span class="truncate text-base-medium text-ink-gray-8">
                      {{ account.account_name }}
                    </span>
                    <Badge
                      variant="subtle"
                      :theme="account.status === 'Active' ? 'green' : 'gray'"
                      :label="__(account.status)"
                    />
                    <Badge
                      v-if="isDefault(account)"
                      variant="outline"
                      theme="blue"
                      :label="__('Default')"
                    />
                  </span>
                  <span class="truncate text-p-sm text-ink-gray-6">
                    {{ __("Phone ID: {0}", [account.phone_id || "-"]) }}
                  </span>
                </button>
                <Dropdown align="end" :options="rowOptions(account)">
                  <Button
                    icon="lucide-more-horizontal"
                    variant="ghost"
                    :aria-label="__('Account actions')"
                  />
                </Dropdown>
              </div>
            </template>
          </div>
          <div
            v-else
            class="flex flex-col items-center gap-3 rounded-6 border border-dashed border-outline-gray-2 px-4 py-10 text-center"
            data-testid="whatsapp-empty-state"
          >
            <div
              class="grid size-10 place-items-center rounded-full bg-surface-gray-2 text-ink-gray-6"
            >
              <span class="lucide-message-circle size-5" aria-hidden="true" />
            </div>
            <div class="flex flex-col gap-1">
              <span class="text-base-medium text-ink-gray-8">
                {{ __("No WhatsApp accounts yet") }}
              </span>
              <span class="max-w-72 text-p-sm text-ink-gray-6">
                {{
                  __(
                    "Add your Meta app's phone number as an account to start receiving messages."
                  )
                }}
              </span>
            </div>
            <Button
              :label="__('Create account')"
              variant="solid"
              icon-left="lucide-plus"
              @click="open('')"
            />
          </div>
        </section>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="confirming"
    :title="__('Unsaved changes')"
    :message="
      __(
        'Are you sure you want to leave the webhook settings? Unsaved changes will be lost.'
      )
    "
    :on-confirm="confirm"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { copyToClipboard } from "@helpdesk/shared/utils";
import {
  Alert,
  Badge,
  Button,
  call,
  createDocumentResource,
  createListResource,
  Dropdown,
  LoadingIndicator,
  Password,
  TextInput,
  toast,
} from "frappe-ui";
import { useUnsavedGuard } from "./useUnsavedGuard";

interface Account {
  name: string;
  account_name: string;
  phone_id: string | null;
  status: "Active" | "Inactive";
}

const emit = defineEmits<{ open: [name: string] }>();

const webhookUrl = `${window.location.origin}/api/method/whatsapp.whatsapp.webhook.handler`;

const accounts = createListResource({
  doctype: "WA Account",
  fields: ["name", "account_name", "phone_id", "status"],
  orderBy: "creation asc",
  pageLength: 99,
  auto: true,
});

const settings = createDocumentResource({
  doctype: "WA Settings",
  name: "WA Settings",
  auto: true,
  setValue: { onError: showError },
});
const { confirming, leave, confirm } = useUnsavedGuard(() => settings.isDirty);

function open(name: string) {
  leave(() => emit("open", name));
}

/** With one account the default is implicit, so it is only named among several. */
function isDefault(account: Account): boolean {
  return (
    accounts.data.length > 1 && account.name === settings.doc?.default_account
  );
}

function rowOptions(account: Account) {
  return [
    {
      label: __("Edit"),
      icon: "lucide-pencil",
      onClick: () => open(account.name),
    },
    {
      label: __("Set as default"),
      icon: "lucide-check-circle",
      condition: () => accounts.data.length > 1 && !isDefault(account),
      onClick: () => setDefault(account),
    },
  ];
}

/** Saves only the default, so unsaved webhook fields stay in the form. */
async function setDefault(account: Account) {
  try {
    await call("frappe.client.set_value", {
      doctype: "WA Settings",
      name: "WA Settings",
      fieldname: "default_account",
      value: account.name,
    });
  } catch (error) {
    return showError(error as { messages?: string[] });
  }
  if (settings.doc) {
    settings.doc.default_account = account.name;
    settings.originalDoc.default_account = account.name;
  }
  toast.success(__("Default account updated"));
}

function saveWebhook() {
  settings.save.submit(undefined, {
    onSuccess: () => toast.success(__("Webhook settings saved")),
  });
}

function showError(error: { messages?: string[] }) {
  toast.error(error?.messages?.[0] || __("Something went wrong"));
}
</script>
