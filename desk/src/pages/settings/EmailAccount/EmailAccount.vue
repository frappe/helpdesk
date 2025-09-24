<template>
  <SettingsHeader :routes="routes" />
  <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
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
            icon-left="plus"
            @click="addEmailAccount"
          />
        </template>
      </SettingsLayoutHeader>
      <!-- list accounts -->
      <div
        v-if="!emailAccounts.loading && Boolean(emailAccounts.data?.length)"
        class="mt-4 divide-y"
      >
        <div
          v-for="emailAccount in emailAccounts.data"
          :key="emailAccount.name"
          @click="
            router.push({
              name: 'EditEmailAccount',
              params: { id: emailAccount.name },
            })
          "
        >
          <EmailAccountCard :emailAccount="emailAccount" />
        </div>
      </div>
      <!-- fallback if no email accounts -->
      <div v-else class="flex items-center justify-center h-64 text-gray-500">
        Please add an email account to continue.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { createListResource } from "frappe-ui";
import SettingsHeader from "../components/SettingsHeader.vue";
import { computed } from "vue";
import { EmailAccount } from "@/types";
import { useRouter } from "vue-router";
import EmailAccountCard from "./components/EmailAccountCard.vue";
import SettingsLayoutHeader from "@/pages/settings/components/SettingsLayoutHeader.vue";

const router = useRouter();

const emailAccounts = createListResource<EmailAccount>({
  doctype: "Email Account",
  cache: ["Email Accounts"],
  fields: ["*"],
  filters: {
    email_id: ["Not Like", "%example%"],
  },
  pageLength: 10,
  auto: true,
  transform: (accounts: EmailAccount[]) => {
    // convert 0 to false to handle boolean fields
    return accounts.forEach((account) => {
      account.enable_incoming = Boolean(account.enable_incoming);
      account.enable_outgoing = Boolean(account.enable_outgoing);
      account.default_incoming = Boolean(account.default_incoming);
      account.default_outgoing = Boolean(account.default_outgoing);
    });
  },
});

const routes = computed(() => [
  {
    label: "Email Accounts",
    route: "/settings/email-accounts",
  },
]);

const addEmailAccount = () => {
  router.push({
    name: "NewEmailAccount",
  });
};
</script>
