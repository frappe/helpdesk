<template>
  <div>
    <!-- header -->
    <SettingsLayoutHeader
      title="Email Accounts"
      description="Manage your email accounts and configure incoming and outgoing settings."
    >
      <template #actions>
        <Button
          label="Add Account"
          theme="gray"
          variant="solid"
          @click="emit('update:step', 'email-add')"
          icon-left="plus"
        />
      </template>
    </SettingsLayoutHeader>
    <!-- list accounts -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="mt-4 divide-y"
    >
      <div v-for="emailAccount in emailAccounts.data" :key="emailAccount.name">
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
      </div>
    </div>
    <!-- fallback if no email accounts -->
    <div v-else class="flex items-center justify-center h-64 text-gray-500">
      Please add an email account to continue.
    </div>
  </div>
</template>

<script setup lang="ts">
import { EmailAccount } from "@/types";
import { createListResource } from "frappe-ui";
import EmailAccountCard from "./EmailAccountCard.vue";
import SettingsLayoutHeader from "./SettingsLayoutHeader.vue";

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
