<template>
  <SettingsLayoutBase
    :title="__('Setup Email')"
    :description="__('Choose the email service provider you want to configure.')"
  >
    <template #content>
      <div class="flex h-full flex-col gap-4">
        <div class="flex flex-col gap-4 overflow-y-auto p-0.5">
          <!-- email service provider selection -->
          <div class="flex flex-wrap items-center gap-4">
            <div
              v-for="s in services"
              :key="s.name"
              class="min-w-3 flex flex-col items-center gap-1"
              @click="handleSelect(s)"
            >
              <EmailProviderIcon
                :service-name="s.name"
                :logo="s.icon"
                :selected="selectedService?.name === s?.name"
              />
            </div>
          </div>
          <div v-if="selectedService" class="flex flex-col gap-4">
            <!-- email service provider info -->
            <div>
              <div class="flex items-center gap-2 rounded-md p-2 ring-1 ring-gray-200">
                <CircleAlert class="h-6 w-5 w-min-5 w-max-5 min-h-5 max-w-5 text-blue-500" />
                <div class="text-wrap text-xs text-gray-700">
                  {{ selectedService.info }}
                  <a :href="selectedService.link" target="_blank" class="text-blue-500 underline">here</a>.
                </div>
              </div>
            </div>
            <!-- service provider fields -->
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
              <div class="grid grid-cols-2 gap-4">
                <div v-for="field in incomingOutgoingFields" :key="field.name" class="flex flex-col gap-1">
                  <FormControl
                    v-model="state[field.name]"
                    :label="field.label"
                    :name="field.name"
                    :type="field.type"
                  />
                  <p class="text-gray-500 text-p-sm">{{ field.description }}</p>
                </div>
              </div>
              <ErrorMessage v-if="error" class="ml-1" :message="error" />
            </div>
          </div>
        </div>

        <!-- action button -->
        <div class="mt-auto flex justify-between -mb-8">
          <Button
            :label="__('Back')"
            theme="gray"
            variant="outline"
            :disabled="addEmailRes.loading"
            @click="emit('update:step', 'email-list')"
          />
          <Button :label="__('Create')" variant="solid" :loading="addEmailRes.loading" @click="createEmailAccount" />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { EmailService, EmailStep } from "@/types";
import { createResource, toast, call } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, reactive, Ref, ref, watch } from "vue";
import CircleAlert from "~icons/lucide/circle-alert";
import {
  customProviderFields,
  incomingOutgoingFields,
  popularProviderFields,
  frappeMailFields,
  services,
  validateInputs,
} from "./emailConfig";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { Link } from "@/components";

type EmailAccountFormState = {
  email_account_name: string;
  email_id: string;
  service: string;
  password?: string;
  api_key?: string;
  api_secret?: string;
  frappe_mail_site?: string;
  domain?: string;
  email_server?: string;
  incoming_port?: string | number;
  smtp_server?: string;
  smtp_port?: string | number;
  use_ssl?: boolean | number;
  use_starttls?: boolean | number;
  use_tls?: boolean | number;
  use_ssl_for_outgoing?: boolean | number;
  validate_ssl_certificate?: boolean | number;
  validate_ssl_certificate_for_outgoing?: boolean | number;
  attachment_limit?: string | number;
  append_emails_to_sent_folder?: boolean | number;
  sent_folder_name?: string;
  enable_incoming: boolean;
  enable_outgoing: boolean;
  default_incoming: boolean;
  default_outgoing: boolean;
};

interface E {
  (event: "update:step", value: EmailStep): void;
}

const emit = defineEmits<E>();

const { updateOnboardingStep } = useOnboarding("helpdesk");

const state = reactive<EmailAccountFormState>({
  service: "",
  email_account_name: "",
  email_id: "",
  password: "",
  api_key: "",
  api_secret: "",
  frappe_mail_site: "",
  enable_incoming: false,
  enable_outgoing: false,
  default_incoming: false,
  default_outgoing: false,
  domain: "",
  email_server: "",
  smtp_server: "",
  incoming_port: "",
  smtp_port: "",
  use_ssl: false,
  use_starttls: false,
  use_tls: false,
  use_ssl_for_outgoing: false,
  validate_ssl_certificate: true,
  validate_ssl_certificate_for_outgoing: true,
  attachment_limit: "",
  append_emails_to_sent_folder: false,
  sent_folder_name: "",
});

const selectedService: Ref<EmailService> = ref(null);
const fields = computed(() => {
  if (!selectedService.value) return [];
  if (selectedService.value.name === "Frappe Mail") {
    return frappeMailFields;
  }
  if (selectedService.value.custom) {
    return customProviderFields;
  }
  return popularProviderFields;
});

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

function handleSelect(service: EmailService) {
  selectedService.value = service;
  state.service = service.name;
  if (!service.custom) {
    state.domain = "";
  }
}

const addEmailRes = createResource({
  url: "helpdesk.api.settings.email.create_email_account",
  makeParams: (val: EmailAccount) => ({ ...val }),
  onSuccess: () => {
    toast.success(__("Email account created"));
    emit("update:step", "email-list");
    updateOnboardingStep("setup_email_account");
  },
  onError: () => {
    error.value = __("Failed to create email account, Invalid credentials");
  },
});

const error = ref<string | undefined>();
function createEmailAccount() {
  error.value = validateInputs(state, state.service);
  if (error.value) return;

  addEmailRes.submit({ data: state });
}

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
