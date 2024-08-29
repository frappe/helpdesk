<template>
  <div>
    <!-- header -->
    <div class="flex items-center justify-between">
      <h1 class="text-lg font-semibold">Email Accounts</h1>
      <Button
        label="Add Account"
        theme="gray"
        variant="solid"
        @click="emit('update:step', 'email-add')"
      >
        <template #prefix>
          <LucidePlus class="h-4 w-4" />
        </template>
      </Button>
    </div>
    <!-- list accounts -->
    <div
      v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
      class="mt-4"
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
import { createListResource } from "frappe-ui";
import EmailAccountCard from "./EmailAccountCard.vue";
import { EmailAccount } from "@/types";

const emit = defineEmits(["update:step"]);

const emailAccounts = createListResource({
  doctype: "Email Account",
  cache: true,
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
