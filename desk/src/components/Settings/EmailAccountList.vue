<template>
  <SettingsLayoutBase
    :title="__('Email Accounts')"
    :description="
      __(
        'Manage your email accounts and configure incoming and outgoing settings.'
      )
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="emit('update:step', 'email-add')"
        icon-left="lucide-plus"
      />
    </template>
    <template #content>
      <!-- list accounts -->
      <div
        class="-ml-2 grow"
        v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      >
        <div class="flex text-sm text-ink-gray-5">
          <div class="ml-2">{{ __("Email account name") }}</div>
        </div>
        <hr class="mx-2 mt-2" />
        <div
          v-for="emailAccount in emailAccounts.data"
          :key="emailAccount.name"
        >
          <EmailAccountCard
            :emailAccount="emailAccount"
            @click="emit('update:step', 'email-edit', emailAccount)"
          />
          <hr
            class="mx-2"
            v-if="
              emailAccount !==
              emailAccounts?.data[emailAccounts?.data?.length - 1]
            "
          />
        </div>
      </div>
      <!-- fallback if no email accounts -->
      <EmptyState
        v-else
        variant="badge"
        :icon="EmailIcon"
        :title="__('No email account found')"
        :description="__('Add one to get started.')"
      />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { EmailAccount } from "@/types";
import { createListResource } from "frappe-ui";
import { EmailIcon } from "../icons";
import EmailAccountCard from "./EmailAccountCard.vue";

const emit = defineEmits(["update:step"]);

const emailAccounts = createListResource({
  doctype: "Email Account",
  cache: ["Email Accounts"],
  fields: ["*"],
  filters: {
    email_id: ["Not Like", "%example%"],
  },
  pageLength: 10,
  auto: true,
  onSuccess: (accounts: EmailAccount[]) => {
    // convert 0 to false to handle boolean fields
    accounts.forEach((account) => {
      account.enable_incoming = Boolean(account.enable_incoming);
      account.enable_outgoing = Boolean(account.enable_outgoing);
      account.default_incoming = Boolean(account.default_incoming);
      account.default_outgoing = Boolean(account.default_outgoing);
    });
  },
});
</script>
