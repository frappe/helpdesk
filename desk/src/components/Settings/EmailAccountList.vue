<template>
  <SettingsLayoutBase
    :title="__('Email Accounts')"
    :description="
      __('Choose the email service provider you want to configure.')
    "
  >
    <template #header-actions>
      <Button
        v-if="!isEmpty"
        :label="__('Add new')"
        theme="gray"
        variant="solid"
        icon-left="plus"
        @click="emit('update:step', 'email-add')"
      />
    </template>
    <template #content>
      <div v-if="emailAccounts.loading" class="flex justify-center pt-10">
        <Button :loading="true" variant="ghost" size="xl" />
      </div>

      <!-- Empty state -->
      <EmailEmptyState v-else-if="isEmpty" @select="onProviderSelect" />

      <!-- Account table -->
      <div v-else class="flex flex-col gap-8">
        <div class="flex flex-col">
          <div
            class="grid grid-cols-[minmax(0,1fr)_140px_140px_40px] items-center gap-3 text-p-sm text-ink-gray-5 pb-2 border-b border-outline-gray-modals"
          >
            <div>{{ __("Name") }}</div>
            <div>{{ __("Status") }}</div>
            <div>{{ __("Date created") }}</div>
            <div></div>
          </div>
          <div
            v-for="account in emailAccounts.data"
            :key="account.name"
            class="grid grid-cols-[minmax(0,1fr)_140px_140px_40px] items-center gap-3 py-3 border-b border-outline-gray-modals last:border-b-0 group"
          >
            <button
              type="button"
              class="flex items-center gap-3 text-left min-w-0"
              @click="emit('update:step', 'email-edit', account)"
            >
              <div class="flex h-7 w-7 items-center justify-center shrink-0">
                <img
                  v-if="emailIcon[account.service]"
                  :src="emailIcon[account.service]"
                  :alt="account.service"
                  class="h-6 w-6 object-contain"
                />
                <LucideMail v-else class="h-5 w-5 text-ink-gray-7" />
              </div>
              <div class="flex flex-col min-w-0">
                <div class="text-p-base text-ink-gray-8 truncate">
                  {{ account.email_id }}
                </div>
                <div class="flex items-baseline gap-1 min-w-0">
                  <LucideTriangleAlert
                    v-if="needsVerification(account)"
                    class="h-3 w-3 shrink-0 self-center text-orange-600"
                  />
                  <span
                    class="text-p-sm truncate"
                    :class="
                      needsVerification(account)
                        ? 'text-orange-600'
                        : 'text-ink-gray-5'
                    "
                  >
                    {{
                      needsVerification(account)
                        ? __("Please verify your email address")
                        : account.email_account_name || account.service
                    }}
                  </span>
                </div>
              </div>
            </button>
            <div>
              <Badge
                v-if="needsVerification(account)"
                variant="subtle"
                theme="orange"
                :label="__('Verify')"
              />
              <Badge
                v-else
                variant="subtle"
                theme="green"
                :label="__('Verified')"
              />
            </div>
            <div class="text-p-sm text-ink-gray-6">
              {{ formatDate(account.creation) }}
            </div>
            <Dropdown :options="rowOptions(account)" placement="right">
              <Button variant="ghost" icon="more-horizontal" />
            </Dropdown>
          </div>
        </div>

        <!-- Default settings -->
        <section class="flex flex-col gap-4">
          <h2 class="text-p-base font-medium text-ink-gray-8">
            {{ __("Default settings") }}
          </h2>
          <SettingsRow
            class="items-center"
            :label="__('Default incoming')"
            :description="
              __(
                'If enabled, all replies to your company (eg: replies@yourcompany.com) will come to this account. Note: Only one account can be default incoming.'
              )
            "
          >
            <Autocomplete
              :model-value="defaultIncoming"
              @update:modelValue="onDefaultChange('incoming', $event)"
              :options="accountOptions"
              class="max-w-56"
              :placeholder="__('Select account')"
            >
              <template #prefix>
                <img
                  v-if="incomingIcon"
                  :src="incomingIcon"
                  class="h-4 w-4 object-contain mr-2"
                />
              </template>
              <template #item-prefix="{ option }">
                <img
                  v-if="option.icon"
                  :src="option.icon"
                  class="h-4 w-4 object-contain mr-2"
                />
              </template>
            </Autocomplete>
          </SettingsRow>
          <SettingsRow
            class="items-center"
            :label="__('Default outgoing')"
            :description="
              __(
                'If enabled, all outgoing emails will be sent from this account. Note: Only one account can be default outgoing.'
              )
            "
          >
            <Autocomplete
              :model-value="defaultOutgoing"
              @update:modelValue="onDefaultChange('outgoing', $event)"
              :options="accountOptions"
              class="max-w-56"
              :placeholder="__('Select account')"
            >
              <template #prefix>
                <img
                  v-if="outgoingIcon"
                  :src="outgoingIcon"
                  class="h-4 w-4 object-contain mr-2"
                />
              </template>
              <template #item-prefix="{ option }">
                <img
                  v-if="option.icon"
                  :src="option.icon"
                  class="h-4 w-4 object-contain mr-2"
                />
              </template>
            </Autocomplete>
          </SettingsRow>
        </section>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import EmailEmptyState from "@/components/EmailEmptyState.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { EmailAccount, EmailAccountListResourceSymbol } from "@/types";
import { ConfirmDelete } from "@/utils";
import dayjs from "dayjs";
import { Autocomplete, Badge, Button, call, Dropdown, toast } from "frappe-ui";
import { computed, inject, markRaw, ref, watch } from "vue";
import LucideMail from "~icons/lucide/mail";
import LucideTriangleAlert from "~icons/lucide/triangle-alert";
import EditIcon from "@/components/icons/EditIcon.vue";
import SettingsRow from "./Email/SettingsRow.vue";
import { emailIcon } from "./emailConfig";

const emit = defineEmits(["update:step"]);

const emailAccounts = inject(EmailAccountListResourceSymbol)!;
const isConfirmingDelete = ref(false);

function onProviderSelect(service: string) {
  const next =
    service === "Custom" ? "email-custom-setup" : "email-provider-setup";
  emit("update:step", next, { service });
}

const isEmpty = computed(
  () => !emailAccounts.loading && !emailAccounts.data?.length
);

const accountOptions = computed(() => [
  { label: __("None"), value: "", icon: "" },
  ...(emailAccounts.data || []).map((account: EmailAccount) => ({
    label: account.email_id,
    value: account.name,
    icon: emailIcon[account.service] || "",
  })),
]);

const defaultIncoming = ref("");
const defaultOutgoing = ref("");

const incomingIcon = computed(() => iconForAccount(defaultIncoming.value));
const outgoingIcon = computed(() => iconForAccount(defaultOutgoing.value));

function iconForAccount(name: string): string {
  const account = (emailAccounts.data || []).find(
    (a: EmailAccount) => a.name === name
  );
  return account ? emailIcon[account.service] || "" : "";
}

function syncDefaults(accounts: EmailAccount[]) {
  defaultIncoming.value = accounts.find((a) => a.default_incoming)?.name || "";
  defaultOutgoing.value = accounts.find((a) => a.default_outgoing)?.name || "";
}

function needsVerification(account: EmailAccount): boolean {
  if (account.awaiting_password) return true;
  return !account.enable_incoming && !account.enable_outgoing;
}

function formatDate(value: string | undefined): string {
  if (!value) return "";
  return dayjs(value).format("DD MMM YYYY");
}

function rowOptions(account: EmailAccount) {
  return [
    {
      label: __("Edit"),
      icon: markRaw(EditIcon),
      onClick: () => emit("update:step", "email-edit", account),
    },
    ...ConfirmDelete({
      onConfirmDelete: () => deleteAccount(account),
      isConfirmingDelete,
    }),
  ];
}

interface CallError {
  message?: string;
  messages?: string[];
}

function errorMessage(err: unknown, fallback: string): string {
  const e = err as CallError;
  return e?.messages?.[0] || e?.message || fallback;
}

function deleteAccount(account: EmailAccount) {
  emailAccounts.delete.submit(account.name, {
    onSuccess: () => toast.success(__("Email account deleted.")),
    onError: (err: unknown) =>
      toast.error(errorMessage(err, __("Failed to delete."))),
  });
}

async function onDefaultChange(
  kind: "incoming" | "outgoing",
  option: { value: string } | null
) {
  const accountName = option?.value || "";
  if (kind === "incoming") defaultIncoming.value = accountName;
  else defaultOutgoing.value = accountName;
  try {
    await call("helpdesk.api.settings.email.set_default_email_account", {
      email_account: accountName,
      kind,
    });
    toast.success(__("Default updated."));
    emailAccounts.reload();
  } catch (err) {
    toast.error(errorMessage(err, __("Failed to update default.")));
  }
}

watch(
  () => emailAccounts.data,
  (data) => {
    if (data) syncDefaults(data as EmailAccount[]);
  },
  { immediate: true }
);
</script>
