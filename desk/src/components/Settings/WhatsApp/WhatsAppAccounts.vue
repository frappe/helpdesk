<template>
  <section class="flex flex-col gap-2">
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
      <template v-for="(account, index) in accounts.data" :key="account.name">
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
        <WhatsAppIcon class="size-5" aria-hidden="true" />
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
    </div>
  </section>
</template>

<script setup lang="ts">
import WhatsAppIcon from "@/components/whatsapp/WhatsAppIcon.vue";
import { __ } from "@/translation";
import {
  Alert,
  Badge,
  Button,
  call,
  createListResource,
  Dropdown,
  LoadingIndicator,
  toast,
} from "frappe-ui";

interface Account {
  name: string;
  account_name: string;
  phone_id: string | null;
  status: "Active" | "Inactive";
}

const props = defineProps<{ settings: any }>();
const emit = defineEmits<{ open: [name: string] }>();

const accounts = createListResource({
  doctype: "WA Account",
  fields: ["name", "account_name", "phone_id", "status"],
  orderBy: "creation asc",
  pageLength: 99,
  auto: true,
});

function open(name: string) {
  emit("open", name);
}

/** With one account the default is implicit, so it is only named among several. */
function isDefault(account: Account): boolean {
  return (
    accounts.data.length > 1 &&
    account.name === props.settings.doc?.default_account
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
  if (props.settings.doc) {
    props.settings.doc.default_account = account.name;
    props.settings.originalDoc.default_account = account.name;
  }
  toast.success(__("Default account updated"));
}

function showError(error: { messages?: string[] }) {
  toast.error(error?.messages?.[0] || __("Something went wrong"));
}
</script>
