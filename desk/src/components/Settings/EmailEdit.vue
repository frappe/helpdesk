<template>
  <SettingsLayoutBase
    :title="__('Edit Email')"
    :description="__('Edit your email account')"
  >
    <template #content>
      <div class="flex h-full flex-col gap-4">
        <div class="overflow-y-auto flex flex-col gap-4 p-0.5">
          <div class="w-fit">
            <EmailProviderIcon
              :logo="emailIcon[state.service || accountData.service]"
              :service-name="state.service || accountData.service"
            />
          </div>
          <div class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200">
            <CircleAlert class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-ink-blue-2" />
            <div class="text-wrap text-xs text-gray-700 flex flex-col gap-1">
              <span>
                {{ info.description }}
                <a :href="info.link" target="_blank" class="text-ink-blue-2 underline">here</a>.
              </span>
              <span v-if="deskEditUrl" class="flex items-center gap-1">
                <a :href="deskEditUrl" target="_blank" class="text-ink-blue-2 underline">
                  {{ __('Open in Desk') }}
                </a>
              </span>
            </div>
          </div>

          <div class="flex flex-col gap-4">
            <div class="grid grid-cols-1 gap-4">
              <div v-for="field in fields" :key="field.name" class="flex flex-col gap-1">
                <div v-if="field.name === 'domain'" class="flex flex-col gap-2">
                  <Link
                    v-model="state.domain"
                    :label="field.label"
                    :placeholder="field.placeholder"
                    doctype="Email Domain"
                    :onCreate="handleCreateDomainClick"
                  />
                  <div v-if="state.domain" class="flex gap-2">
                    <Button
                      size="sm"
                      variant="subtle"
                      theme="gray"
                      :label="__('Edit Domain')"
                      @click="handleEditDomainClick"
                    />
                  </div>
                </div>
                <FormControl
                  v-else
                  v-model="state[field.name]"
                  :label="field.label"
                  :name="field.name"
                  :type="field.type"
                  :placeholder="field.placeholder"
                />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="field in incomingOutgoingFields" :key="field.name" class="flex flex-col gap-1">
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
        </div>

        <div class="mt-auto flex justify-between -mb-8">
          <Button
            :label="__('Back')"
            theme="gray"
            variant="outline"
            :disabled="loading"
            @click="emit('update:step', 'email-list')"
          />
          <div class="flex gap-2">
            <Button :label="__('Update Account')" variant="solid" @click="updateAccount" :loading="loading" />
            <Button
              v-if="accountData.enable_incoming"
              :label="__('Pull Emails')"
              variant="subtle"
              @click="pullEmails"
              :loading="loadingPull"
              :disabled="loading"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { EmailAccount, EmailStep } from "@/types";
import { useStorage } from "@vueuse/core";
import { call, toast } from "frappe-ui";
import { computed, h, reactive, ref, watch } from "vue";
import CircleAlert from "~icons/lucide/circle-alert";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import {
  customProviderFields,
  emailIcon,
  incomingOutgoingFields,
  popularProviderFields,
  services,
  validateInputs,
  frappeMailFields,
} from "./emailConfig";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { Link } from "@/components";

type EmailAccountFormState = {
  email_account_name: string;
  service: string;
  email_id: string;
  api_key?: string | null;
  api_secret?: string | null;
  password?: string | null;
  frappe_mail_site?: string;
  domain?: string;
  email_server?: string;
  smtp_server?: string;
  incoming_port?: string | number;
  smtp_port?: string | number;
  use_ssl?: boolean | number;
  use_starttls?: boolean | number;
  use_tls?: boolean | number;
  use_ssl_for_outgoing?: boolean | number;
  validate_ssl_certificate?: boolean | number;
  validate_ssl_certificate_for_outgoing?: boolean | number;
  enable_incoming: boolean;
  enable_outgoing: boolean;
  default_outgoing: boolean;
  default_incoming: boolean;
  attachment_limit?: string | number;
  append_emails_to_sent_folder?: boolean | number;
  sent_folder_name?: string;
};

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

const state = reactive<EmailAccountFormState>({
  email_account_name: props.accountData.email_account_name || "",
  service: props.accountData.service || "",
  email_id: props.accountData.email_id || "",
  api_key: props.accountData?.api_key || null,
  api_secret: props.accountData?.api_secret || null,
  password: props.accountData?.password || null,
  frappe_mail_site: props.accountData?.frappe_mail_site || "",
  domain: props.accountData?.domain || "",
  email_server: props.accountData?.email_server || "",
  smtp_server: props.accountData?.smtp_server || "",
  incoming_port: props.accountData?.incoming_port || "",
  smtp_port: props.accountData?.smtp_port || "",
  use_ssl: props.accountData?.use_ssl || false,
  use_starttls: props.accountData?.use_starttls || false,
  use_tls: props.accountData?.use_tls || false,
  use_ssl_for_outgoing: props.accountData?.use_ssl_for_outgoing || false,
  validate_ssl_certificate: props.accountData?.validate_ssl_certificate ?? true,
  validate_ssl_certificate_for_outgoing:
    props.accountData?.validate_ssl_certificate_for_outgoing ?? true,
  enable_incoming: props.accountData.enable_incoming || false,
  enable_outgoing: props.accountData.enable_outgoing || false,
  default_outgoing: props.accountData.default_outgoing || false,
  default_incoming: props.accountData.default_incoming || false,
  attachment_limit: (props.accountData as any)?.attachment_limit || "",
  append_emails_to_sent_folder:
    (props.accountData as any)?.append_emails_to_sent_folder || false,
  sent_folder_name: (props.accountData as any)?.sent_folder_name || "",
});

const info = {
  description: __("To know more about setting up email accounts, click"),
  link: "https://docs.erpnext.com/docs/user/manual/en/email-account",
};

const deskEditUrl = computed(() => {
  const name = state.email_account_name || props.accountData.email_account_name;
  if (!name) return "";
  return `/desk/email-account/${encodeURIComponent(name)}`;
});

const serviceDef = computed(() => {
  const currentService = state.service || props.accountData.service;
  return services.find((s) => s.name === currentService);
});

const isCustomProvider = computed(() => {
  if (serviceDef.value) return serviceDef.value.custom;
  // Many existing custom accounts store service as blank; detect by server fields.
  return Boolean(
    state.email_server ||
      state.smtp_server ||
      props.accountData.email_server ||
      props.accountData.smtp_server
  );
});

const fields = computed(() => {
  if (isCustomProvider.value) {
    return customProviderFields;
  }
  if (!serviceDef.value) {
    return popularProviderFields;
  }
  if (serviceDef.value.name === "Frappe Mail") {
    return frappeMailFields;
  }
  return popularProviderFields;
});

const error = ref<string | undefined>();
const loading = ref(false);
const loadingPull = useStorage(`loading-emails-${state.email_account_name}`, false);

async function updateAccount() {
  error.value = validateInputs(state, state.service || serviceDef.value?.name || "", true);
  if (error.value) return;
  const old = { ...props.accountData };
  const updatedEmailAccount = { ...state };

  const nameChanged = old.email_account_name !== updatedEmailAccount.email_account_name;
  delete old.email_account_name;
  delete updatedEmailAccount.email_account_name;

  const otherFieldsChanged = isDirty.value;
  const values = updatedEmailAccount;

  if (!nameChanged && !otherFieldsChanged) {
    toast.create({
      message: __("No changes made"),
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
    message: __("Pulling emails, this may take a few minutes."),
    icon: h(CircleAlert, { class: "text-blue-500" }),
  });

  call("frappe.email.doctype.email_account.email_account.pull_emails", {
    email_account: state.email_account_name,
  })
    .then(() => {
      localStorage.removeItem(`loading-emails-${state.email_account_name}`);
      loadingPull.value = null;
      toast.success(__("Emails pulled successfully"));
    })
    .catch(() => {
      localStorage.removeItem(`loading-emails-${state.email_account_name}`);
      loadingPull.value = null;
      error.value = __("Failed to pull emails");
    });
}

const isDirty = computed(() => {
  return (
    state.domain !== props.accountData.domain ||
    state.service !== props.accountData.service ||
    state.email_id !== props.accountData.email_id ||
    state.api_key !== props.accountData.api_key ||
    state.api_secret !== props.accountData.api_secret ||
    state.password !== props.accountData.password ||
    state.email_server !== props.accountData.email_server ||
    state.smtp_server !== props.accountData.smtp_server ||
    state.incoming_port !== props.accountData.incoming_port ||
    state.smtp_port !== props.accountData.smtp_port ||
    state.use_ssl !== props.accountData.use_ssl ||
    state.use_starttls !== props.accountData.use_starttls ||
    state.enable_incoming !== props.accountData.enable_incoming ||
    state.enable_outgoing !== props.accountData.enable_outgoing ||
    state.default_outgoing !== props.accountData.default_outgoing ||
    state.default_incoming !== props.accountData.default_incoming ||
    state.frappe_mail_site !== props.accountData.frappe_mail_site
  );
});

async function callRenameDoc() {
  return call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: props.accountData.email_account_name,
    new_name: state.email_account_name,
  });
}

async function callSetValue(values: Record<string, any>) {
  const d = await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: state.email_account_name,
    fieldname: values,
  });
  return d.name;
}

function succesHandler() {
  emit("update:step", "email-list");
  toast.success(__("Email account updated successfully"));
}

function errorHandler() {
  loading.value = false;
  error.value = __("Failed to update email account, Invalid credentials");
}

watch(
  () => props.accountData,
  (val) => {
    if (!val) return;
    if (val.email_id && state.email_id !== val.email_id) {
      state.email_id = val.email_id;
    }
    if (!state.domain && val.domain) {
      state.domain = val.domain;
    }
  },
  { deep: true, immediate: true }
);

watch(
  () => state.domain,
  async (val) => {
    if (!val) return;
    try {
      const doc = await call("frappe.client.get", {
        doctype: "Email Domain",
        name: val,
      });
      syncAccountFieldsFromDomain(doc);
    } catch (err) {
      console.warn("Failed to load Email Domain", err);
    }
  }
);

function syncAccountFieldsFromDomain(payload: Record<string, any>) {
  state.email_server = payload.email_server ?? state.email_server;
  state.smtp_server = payload.smtp_server ?? state.smtp_server;
  state.incoming_port = payload.incoming_port ?? state.incoming_port;
  state.smtp_port = payload.smtp_port ?? state.smtp_port;
  state.use_ssl = Boolean(payload.use_ssl ?? state.use_ssl);
  state.use_starttls = Boolean(payload.use_starttls ?? state.use_starttls);
  state.use_tls = Boolean(payload.use_tls ?? state.use_tls);
  state.use_ssl_for_outgoing = Boolean(payload.use_ssl_for_outgoing ?? state.use_ssl_for_outgoing);
  state.validate_ssl_certificate = Boolean(payload.validate_ssl_certificate ?? state.validate_ssl_certificate);
  state.validate_ssl_certificate_for_outgoing = Boolean(
    payload.validate_ssl_certificate_for_outgoing ?? state.validate_ssl_certificate_for_outgoing
  );
  state.append_emails_to_sent_folder = Boolean(
    payload.append_emails_to_sent_folder ?? state.append_emails_to_sent_folder
  );
  state.sent_folder_name = payload.sent_folder_name || state.sent_folder_name;
  state.attachment_limit = payload.attachment_limit || state.attachment_limit;
}

function handleCreateDomainClick(value: any, close?: () => void) {
  close?.();
  window.open("/desk/email-domain/new-email-domain", "_blank", "noopener,noreferrer");
}

function handleEditDomainClick() {
  if (!state.domain) return;
  window.open(`/desk/email-domain/${encodeURIComponent(state.domain)}`, "_blank", "noopener,noreferrer");
}
</script>

<style scoped></style>
