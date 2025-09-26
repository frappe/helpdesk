<template>
  <SettingsHeader :routes="routes" />
  <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
    <div class="flex h-full flex-col gap-4">
      <!-- title and desc -->
      <div role="heading" aria-level="1" class="flex gap-1 justify-between">
        <h5 class="text-lg font-semibold">Edit Email</h5>
      </div>
      <div class="w-fit">
        <EmailProviderIcon
          :logo="emailIcon[emailAccountData.service]"
          :service-name="emailAccountData.service"
        />
      </div>
      <!-- banner for setting up email account -->
      <div class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200">
        <CircleAlert
          class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-ink-blue-2"
        />
        <div class="text-wrap text-xs text-gray-700">
          {{ info.description }}
          <a :href="info.link" target="_blank" class="text-ink-blue-2 underline"
            >here</a
          >
          .
        </div>
      </div>
      <!-- fields -->
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4">
          <div
            v-for="field in fields"
            :key="field.name"
            class="flex flex-col gap-1"
          >
            <FormControl
              v-model="emailAccountData[field.name]"
              :label="field.label"
              :name="field.name"
              :type="field.type"
              :placeholder="field.placeholder"
            />
          </div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div
            v-for="field in incomingOutgoingFields"
            :key="field.name"
            class="flex flex-col gap-1"
          >
            <FormControl
              v-model="emailAccountData[field.name]"
              :label="field.label"
              :name="field.name"
              :type="field.type"
            />
            <p class="text-p-sm text-gray-500">{{ field.description }}</p>
          </div>
        </div>
        <ErrorMessage v-if="error" class="ml-1" :message="error" />
      </div>
      <!-- action buttons -->
      <div class="mt-auto flex justify-between">
        <Button
          label="Back"
          theme="gray"
          variant="outline"
          :disabled="loading"
        />
        <div class="flex gap-2">
          <Button
            label="Update Account"
            variant="solid"
            @click="updateAccount"
            :loading="loading"
            :disabled="!isDirty"
          />
          <Button
            v-if="emailAccountData.enable_incoming"
            label="Pull Emails"
            variant="subtle"
            @click="pullEmails"
            :loading="loadingPull"
            :disabled="loading"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SettingsHeader from "../components/SettingsHeader.vue";
import { useStorage } from "@vueuse/core";
import { call, createResource, toast } from "frappe-ui";
import { computed, h, ref, watch } from "vue";
import CircleAlert from "~icons/lucide/circle-alert";
import EmailProviderIcon from "./components/EmailProviderIcon.vue";
import {
  customProviderFields,
  emailIcon,
  incomingOutgoingFields,
  popularProviderFields,
  services,
  validateInputs,
} from "./emailConfig";
import { useRouter } from "vue-router";

const emailAccountData = ref({
  email_account_name: "",
  service: "",
  email_id: "",
  api_key: null,
  api_secret: null,
  password: null,
  frappe_mail_site: "",
  enable_incoming: false,
  enable_outgoing: false,
  default_outgoing: false,
  default_incoming: false,
});
const initialData = ref("");
const router = useRouter();

const getEmailAccountData = createResource({
  url: "frappe.client.get",
  params: {
    doctype: "Email Account",
    name: router.currentRoute.value.params.id,
  },
  auto: true,
  onSuccess(data) {
    emailAccountData.value = {
      ...data,
      enable_incoming: Boolean(data.enable_incoming),
      enable_outgoing: Boolean(data.enable_outgoing),
      default_outgoing: Boolean(data.default_outgoing),
      default_incoming: Boolean(data.default_incoming),
    };
    initialData.value = JSON.stringify(emailAccountData.value);
  },
});

const routes = computed(() => [
  {
    label: "Email Accounts",
    route: "/settings/email-accounts",
  },
  {
    label: getEmailAccountData.data?.email_account_name,
    route: `/settings/email-accounts/${getEmailAccountData.data?.email_account_name}`,
  },
]);

const info = {
  description: "To know more about setting up email accounts, click",
  link: "https://docs.erpnext.com/docs/user/manual/en/email-account",
};

const isCustomService = computed(() => {
  return services.find((s) => s.name === emailAccountData.value.service)
    ?.custom;
});

const fields = computed(() => {
  if (isCustomService.value) {
    return customProviderFields;
  }
  return popularProviderFields;
});

const error = ref<string | undefined>();
const loading = ref(false);
const isDirty = ref(false);
const loadingPull = useStorage(
  `loading-emails-${emailAccountData.value.email_account_name}`,
  false
);

async function updateAccount() {
  error.value = validateInputs(emailAccountData.value, isCustomService.value);
  if (error.value) return;
  const old = { ...emailAccountData.value };
  const updatedEmailAccount = { ...emailAccountData.value };

  const nameChanged =
    old.email_account_name !== updatedEmailAccount.email_account_name;
  delete old.email_account_name;
  delete updatedEmailAccount.email_account_name;

  const otherFieldsChanged = isDirty.value;
  const values = updatedEmailAccount;

  if (!nameChanged && !otherFieldsChanged) {
    toast.create({
      message: "No changes made",
      icon: h(CircleAlert, { class: "text-ink-blue-2" }),
    });
    return;
  }

  if (nameChanged) {
    try {
      loading.value = true;
      await callRenameDoc();
      succesHandler();
    } catch (err) {
      errorHandler();
    }
  }
  if (otherFieldsChanged) {
    try {
      loading.value = true;
      await callSetValue(values);
      succesHandler();
    } catch (err) {
      errorHandler();
    }
  }
}

function pullEmails() {
  loadingPull.value = true;

  toast.create({
    message: "Pulling emails, this may take a few minutes.",
    icon: h(CircleAlert, { class: "text-blue-500" }),
  });

  call("frappe.email.doctype.email_account.email_account.pull_emails", {
    email_account: emailAccountData.value.email_account_name,
  })
    .then(() => {
      localStorage.removeItem(
        `loading-emails-${emailAccountData.value.email_account_name}`
      );
      loadingPull.value = null;
      toast.success("Emails pulled successfully");
    })
    .catch(() => {
      localStorage.removeItem(
        `loading-emails-${emailAccountData.value.email_account_name}`
      );
      loadingPull.value = null;
      error.value = "Failed to pull emails";
    });
}

watch(
  emailAccountData,
  (newData) => {
    if (initialData.value) {
      isDirty.value = JSON.stringify(newData) !== initialData.value;
    }
  },
  { deep: true }
);

async function callRenameDoc() {
  const d = await call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: getEmailAccountData.data.email_account_name,
    new_name: emailAccountData.value.email_account_name,
  });
  return d;
}

async function callSetValue(values) {
  const d = await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: emailAccountData.value.email_account_name,
    fieldname: values,
  });
  return d.name;
}

function succesHandler() {
  toast.success("Email account updated successfully");
}

function errorHandler() {
  loading.value = false;
  error.value = "Failed to update email account, Invalid credentials";
}
</script>
