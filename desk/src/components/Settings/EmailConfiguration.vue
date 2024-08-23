<template>
  <div class="flex h-full flex-col gap-4">
    <!-- title and desc -->
    <div role="heading" aria-level="1" class="flex flex-col gap-1">
      <h5 class="text-lg font-semibold">Setup Email</h5>
      <p class="text-sm text-gray-600">
        Choose the email service provider you want to configure.
      </p>
    </div>
    <!-- email service provider selection -->
    <div class="flex flex-wrap items-center gap-4">
      <div
        v-for="s in services"
        :key="s.name"
        class="min-w-3 flex flex-col items-center gap-1"
        @click="() => (selectedService = s)"
      >
        <div
          class="flex h-10 w-10 cursor-pointer items-center justify-center rounded-xl bg-gray-100 hover:bg-gray-200"
          :class="{
            'ring-2 ring-blue-500': s.name === selectedService?.name,
          }"
        >
          <img :src="s.icon" class="h-6 w-6" />
        </div>
        <p class="text-center text-xs text-gray-700">{{ s.name }}</p>
      </div>
    </div>
    <div v-if="selectedService" class="flex flex-col gap-4">
      <!-- email service provider info -->
      <div
        class="flex items-center justify-center gap-2 rounded-md p-2 ring-1 ring-gray-200"
      >
        <IconAlert class="h-8 min-w-[5%] text-blue-500" />
        <div class="text-wrap text-xs text-gray-700">
          {{ selectedService.info }}
          <a
            :href="selectedService.link"
            target="_blank"
            class="text-blue-500 underline"
            >here</a
          >
          .
        </div>
      </div>
      <!-- service provider fields -->
      <div v-if="popularProviders.includes(selectedService.name)">
        <div class="flex flex-col gap-2">
          <div class="grid grid-cols-1 gap-4">
            <div
              v-for="field in emailFields.popularProviders"
              :key="field.name"
              class="flex flex-col gap-1"
            >
              <FormControl
                v-model="state[field.name]"
                :label="field.label"
                :name="field.name"
                :type="field.type"
                :placeholder="field.placeholder"
              />
            </div>
          </div>
          <ErrorMessage v-if="error" class="ml-1" :message="error" />
        </div>
      </div>
    </div>
    <div v-if="selectedService" class="mt-auto flex flex-row-reverse">
      <Button
        label="Create"
        variant="solid"
        :loading="insertRes.loading"
        size="md"
        @click="createEmailAccount"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { createResource, debounce } from "frappe-ui";
import IconAlert from "~icons/espresso/alert-circle";
import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";
import zod from "zod";
import { useError } from "@/composables/error";
import { createToast } from "@/utils";

const services = [
  {
    name: "GMail",
    icon: LogoGmail,
    info: `Setting up GMail requires you to enable two factor authentication
		and app specific passwords. Read more`,
    link: "https://support.google.com/accounts/answer/185833",
    custom: false,
  },
  {
    name: "Outlook",
    icon: LogoOutlook,
    info: `Setting up Outlook requires you to enable two factor authentication
		and app specific passwords. Read more`,
    link: "https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944",
    custom: false,
  },
  {
    name: "Sendgrid",
    icon: LogoSendgrid,
    info: `Setting up Sendgrid requires you to enable two factor authentication
		and app specific passwords. Read more `,
    link: "https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/",
    custom: false,
  },
  {
    name: "SparkPost",
    icon: LogoSparkpost,
    info: `Setting up SparkPost requires you to enable two factor authentication
		and app specific passwords. Read more `,
    link: "https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication",
    custom: false,
  },
  {
    name: "Yahoo",
    icon: LogoYahoo,
    info: `Setting up Yahoo requires you to enable two factor authentication
		and app specific passwords. Read more `,
    link: "https://help.yahoo.com/kb/SLN15241.html",
    custom: false,
  },
  {
    name: "Yandex",
    icon: LogoYandex,
    info: `Setting up Yandex requires you to enable two factor authentication
		and app specific passwords. Read more `,
    link: "https://yandex.com/support/id/authorization/app-passwords.html",
    custom: false,
  },
];

const selectedService = ref(null);

const customProviders = ["Frappe Mail"];
const popularProviders = [
  "GMail",
  "Outlook",
  "Sendgrid",
  "SparkPost",
  "Yahoo",
  "Yandex",
];

const state = reactive({
  email_account_name: "sak",
  email_id: "ksd@gk.com",
  password: "123",
  api_key: "",
  api_secret: "",
});

const emailFields = {
  popularProviders: [
    {
      label: "Account Name",
      name: "email_account_name",
      type: "text",
      placeholder: "Support / Sales",
    },
    {
      label: "Email ID",
      name: "email_id",
      type: "email",
      placeholder: "johndoe@example.com",
    },
    {
      label: "App Password",
      name: "password",
      type: "password",
      placeholder: "********",
    },
  ],
  customProviders: [
    {
      label: "Account Name",
      name: "email_account_name",
      type: "text",
      placeholder: "Support / Sales",
    },
    {
      label: "Email ID",
      name: "email_id",
      type: "email",
      placeholder: "johndoe@example.com",
    },
    {
      label: "API Key",
      name: "api_key",
      type: "text",
      placeholder: "********",
    },
    {
      label: "API Secret",
      name: "api_secret",
      type: "password",
      placeholder: "********",
    },
  ],
};
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
    state.email_account_name = "";
    state.email_id = "";
    state.password = "";
    state.api_key = "";
    state.api_secret = "";
    createToast({
      title: "Assignment cleared successfully",
      icon: "check",
      iconClasses: "text-green-600",
    });
  },
  onError: (e) => {
    createToast({
      title: "Failed to create email account, Invalid credentials",
      icon: "alert-circle",
      iconClasses: "text-red-600",
    });
  },
});

const submit = debounce(() => {
  insertRes.submit({
    doc: {
      doctype: "Email Account",

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
      service: selectedService.value.name,
      use_tls: 1,
      use_imap: 1,
      smtp_port: 587,
      ...state,
      ...emailDefaults[selectedService.value.name],
    },
  });
}, 500);

const error = ref("");
function createEmailAccount() {
  validateInputs();
  if (error.value) return;
  submit();
}

function validateInputs() {
  if (!state.email_account_name) {
    error.value = "Account name is required";
    return;
  }
  if (!state.email_id) {
    error.value = "Email ID is required";
    return;
  }
  const validEmail = zod.string().email().safeParse(state.email_id).success;
  if (!validEmail) {
    error.value = "Invalid email ID";
    return;
  }
  if (!state.password) {
    error.value = "Password is required";
    return;
  }
  error.value = "";
}
</script>

<style scoped></style>
