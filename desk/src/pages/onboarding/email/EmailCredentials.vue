<template>
  <div class="flex flex-col gap-4">
    <form class="space-y-4" @submit.prevent="submit">
      <Input
        v-model="accountName"
        label="Account name"
        placeholder="John Doe (Example.com)"
        type="text"
        required
      />
      <Input
        v-model="email"
        label="Email"
        placeholder="john.doe@example.com"
        type="email"
        required
      />
      <Input
        v-model="password"
        label="Password"
        placeholder="••••••••"
        type="password"
        required
      />
    </form>
    <Button
      label="Finish!"
      :disabled="!accountName || !email || !password"
      :loading="insertRes.loading"
      class="w-max"
      variant="outline"
      @click="submit"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import { createResource, Button, Input, debounce } from "frappe-ui";
import { capture } from "@/telemetry";
import { useError } from "@/composables/error";
import { useOnboardingEmailStore } from "./data";

const onboardingEmailStore = useOnboardingEmailStore();
const { next } = onboardingEmailStore;
const { service } = storeToRefs(onboardingEmailStore);
const accountName = ref("");
const email = ref("");
const password = ref("");

const emailDefaults = {
  GMail: {
    email_server: "imap.gmail.com",
    use_ssl: 1,
    smtp_server: "smtp.gmail.com",
  },
  outlook: {
    email_server: "imap-mail.outlook.com",
    use_ssl: 1,
    smtp_server: "smtp-mail.outlook.com",
  },
  Sendgrid: {
    smtp_server: "smtp.sendgrid.net",
    smtp_port: 587,
  },
  SparkPost: {
    smtp_server: "smtp.sparkpostmail.com",
  },
  Yahoo: {
    email_server: "imap.mail.yahoo.com",
    use_ssl: 1,
    smtp_server: "smtp.mail.yahoo.com",
    smtp_port: 587,
  },
  Yandex: {
    email_server: "imap.yandex.com",
    use_ssl: 1,
    smtp_server: "smtp.yandex.com",
    smtp_port: 587,
  },
};

const insertRes = createResource({
  url: "frappe.client.insert",
  onSuccess: () => {
    capture("onboarding_email_credentials_success");
    next();
  },
  onError: (e) => {
    useError()(e);
    capture("onboarding_email_credentials_fail");
  },
});

const submit = debounce(() => {
  insertRes.submit({
    doc: {
      doctype: "Email Account",
      email_account_name: accountName.value,
      email_id: email.value,
      password: password.value,
      enable_incoming: true,
      enable_outgoing: true,
      default_incoming: true,
      default_outgoing: true,
      email_sync_option: "ALL",
      initial_sync_count: 100,
      imap_folder: [
        {
          append_to: "HD Ticket",
          folder_name: "INBOX",
        },
      ],
      create_contact: true,
      track_email_status: true,
      service: service.value,
      use_tls: 1,
      use_imap: 1,
      smtp_port: 587,
      ...emailDefaults[service.value],
    },
  });
}, 500);

onMounted(() => capture("onboarding_email_credentials_reached"));
</script>
