<template>
  <div class="flex h-full flex-col gap-4">
    <!-- title and desc -->
    <div
      role="heading"
      aria-level="1"
      class="flex gap-1 justify-between pt-[5px]"
    >
      <h5 class="text-lg font-semibold">Edit Email</h5>
    </div>
    <div class="w-fit">
      <EmailProviderIcon
        :logo="emailIcon[accountData.service]"
        :service-name="accountData.service"
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
            v-model="state[field.name]"
            :label="field.label"
            :name="field.name"
            :type="field.type"
            :placeholder="field.placeholder"
          />
        </div>
      </div>
      <div class="grid grid-cols-2 gap-4">
        <div
          v-for="field in incomingOutgoingFields"
          :key="field.name"
          class="flex flex-col gap-1"
        >
          <FormControl
            v-model="state[field.name]"
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
        @click="emit('update:step', 'email-list')"
      />
      <div class="flex gap-2">
        <Button
          label="Update Account"
          variant="solid"
          @click="updateAccount"
          :loading="loading"
        />
        <Button
          v-if="accountData.enable_incoming"
          label="Pull Emails"
          variant="subtle"
          @click="pullEmails"
          :loading="loadingPull"
          :disabled="loading"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { EmailAccount, EmailStep } from "@/types";
import { useStorage } from "@vueuse/core";
import { call, toast } from "frappe-ui";
import { computed, h, reactive, ref } from "vue";
import CircleAlert from "~icons/lucide/circle-alert";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import {
  customProviderFields,
  emailIcon,
  incomingOutgoingFields,
  popularProviderFields,
  services,
  validateInputs,
} from "./emailConfig";

interface P {
  accountData: EmailAccount;
}

interface E {
  (event: "update:step", step: EmailStep): void;
}

const props = withDefaults(defineProps<P>(), {
  accountData: null,
});

const emit = defineEmits<E>();

const state = reactive({
  email_account_name: props.accountData.email_account_name || "",
  service: props.accountData.service || "",
  email_id: props.accountData.email_id || "",
  api_key: props.accountData?.api_key || null,
  api_secret: props.accountData?.api_secret || null,
  password: props.accountData?.password || null,
  frappe_mail_site: props.accountData?.frappe_mail_site || "",
  enable_incoming: props.accountData.enable_incoming || false,
  enable_outgoing: props.accountData.enable_outgoing || false,
  default_outgoing: props.accountData.default_outgoing || false,
  default_incoming: props.accountData.default_incoming || false,
});

const info = {
  description: "To know more about setting up email accounts, click",
  link: "https://docs.erpnext.com/docs/user/manual/en/email-account",
};

const isCustomService = computed(() => {
  return services.find((s) => s.name === props.accountData.service).custom;
});

const fields = computed(() => {
  if (isCustomService.value) {
    return customProviderFields;
  }
  return popularProviderFields;
});

const error = ref<string | undefined>();
const loading = ref(false);
const loadingPull = useStorage(
  `loading-emails-${state.email_account_name}`,
  false
);
async function updateAccount() {
  error.value = validateInputs(state, isCustomService.value);
  if (error.value) return;
  const old = { ...props.accountData };
  const updatedEmailAccount = { ...state };

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
    email_account: state.email_account_name,
  })
    .then(() => {
      localStorage.removeItem(`loading-emails-${state.email_account_name}`);
      loadingPull.value = null;
      toast.success("Emails pulled successfully");
    })
    .catch(() => {
      localStorage.removeItem(`loading-emails-${state.email_account_name}`);
      loadingPull.value = null;
      error.value = "Failed to pull emails";
    });
}

const isDirty = computed(() => {
  return (
    state.email_id !== props.accountData.email_id ||
    state.api_key !== props.accountData.api_key ||
    state.api_secret !== props.accountData.api_secret ||
    state.password !== props.accountData.password ||
    state.enable_incoming !== props.accountData.enable_incoming ||
    state.enable_outgoing !== props.accountData.enable_outgoing ||
    state.default_outgoing !== props.accountData.default_outgoing ||
    state.default_incoming !== props.accountData.default_incoming ||
    state.frappe_mail_site !== props.accountData.frappe_mail_site
  );
});

async function callRenameDoc() {
  const d = await call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: props.accountData.email_account_name,
    new_name: state.email_account_name,
  });
  return d;
}

async function callSetValue(values) {
  const d = await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: state.email_account_name,
    fieldname: values,
  });
  return d.name;
}

function succesHandler() {
  emit("update:step", "email-list");
  toast.success("Email account updated successfully");
}

function errorHandler() {
  loading.value = false;
  error.value = "Failed to update email account, Invalid credentials";
}
</script>
