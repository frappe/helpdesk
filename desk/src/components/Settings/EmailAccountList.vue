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
      class="mt-8 divide-y"
    >
      <div v-for="emailAccount in emailAccounts.data" :key="emailAccount.name">
        <EmailAccountCard
          :emailAccount="emailAccount"
          @click="emit('update:step', 'email-edit', emailAccount)"
        />
      </div>
    </div>
    <!-- fallback if no email accounts -->
    <div
      v-else
      class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
    >
      <div
        class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
      >
        <EmailIcon class="size-6 text-ink-gray-6" />
      </div>
      <div class="flex flex-col items-center gap-1">
        <div class="text-base font-medium text-ink-gray-6">
          No email account found
        </div>
        <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
          Add your first account to get started.
        </div>
      </div>
      <Button
        label="Add Email Account"
        variant="outline"
        icon-left="plus"
        @click="emit('update:step', 'email-add')"
      />
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
