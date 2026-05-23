<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-1 justify-center -ml-[16px]">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="__('Add custom mail')"
            size="md"
            :disabled="createAccount.loading"
            @click="emit('update:step', backStep)"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
          />
        </div>
      </div>
    </template>
    <template #header-actions>
      <div class="flex items-center gap-2">
        <Button
          :label="__('Cancel')"
          theme="gray"
          variant="outline"
          :disabled="createAccount.loading"
          @click="emit('update:step', 'email-list')"
        />
        <Button
          :label="__('Save')"
          variant="solid"
          :loading="createAccount.loading"
          @click="save"
        />
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormControl
            v-model="state.email_account_name"
            :label="__('Account name')"
            type="text"
            :placeholder="__('Support / Sales')"
          />
          <FormControl
            v-model="state.email_id"
            :label="__('Email')"
            type="email"
            placeholder="johndoe@example.com"
          />
          <div class="flex flex-col gap-2">
            <Link
              v-model="state.domain"
              :label="__('Domain name')"
              :placeholder="__('e.g. name.example.com')"
              doctype="Email Domain"
              :onCreate="(_value: unknown, close?: () => void) => openDomainCreate(close)"
            />
            <Button
              v-if="state.domain"
              size="sm"
              variant="subtle"
              theme="gray"
              :label="__('Edit Domain')"
              class="self-start"
              @click="() => openDomainEdit(state.domain)"
            />
          </div>
          <div class="flex flex-col gap-1">
            <FormControl
              v-model="state.reply_to"
              :label="__('Reply-to Email address')"
              type="email"
              :placeholder="__('e.g name.example.com')"
            />
            <p class="text-p-sm text-ink-gray-5 flex items-center gap-1">
              <LucideInfo class="h-3.5 w-3.5" />
              {{ __("This will be your reply-to email address.") }}
            </p>
          </div>
        </div>

        <CustomServerSection
          :title="__('Incoming Settings')"
          :server-label="__('Incoming Email Server Domain')"
          :server-placeholder="__('imap.example.com')"
          :port-label="__('IMAP Port')"
          port-placeholder="993"
          :port-hint="__('e.g. POP3: 995/110, IMAP: 993/143')"
          v-model:server="state.email_server"
          v-model:port="state.incoming_port"
          v-model:login="state.incoming_login"
          v-model:password="state.incoming_password"
          v-model:useSsl="state.use_ssl"
        >
          <template #extras>
            <label class="flex items-center gap-2">
              <FormControl v-model="state.use_imap" type="checkbox" />
              <span class="text-p-sm text-ink-gray-7">{{
                __("Use IMAP")
              }}</span>
            </label>
          </template>
        </CustomServerSection>

        <CustomServerSection
          :title="__('Outgoing settings')"
          :server-label="__('Outgoing Email Server Domain')"
          :server-placeholder="__('smtp.example.com')"
          :port-label="__('SMTP Port')"
          port-placeholder="587"
          :port-hint="__('If non standard port (e.g. 587)')"
          v-model:server="state.smtp_server"
          v-model:port="state.smtp_port"
          v-model:login="state.outgoing_login"
          v-model:password="state.outgoing_password"
          v-model:useSsl="state.use_ssl_for_outgoing"
        />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { EmailStep } from "@/types";
import { validateEmailWithZod } from "@/utils";
import { Button, createResource, FormControl, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { reactive, watch } from "vue";
import LucideInfo from "~icons/lucide/info";
import CustomServerSection from "./Email/CustomServerSection.vue";
import {
  openDomainCreate,
  openDomainEdit,
  syncCustomServerFromDomain,
} from "./Email/domainSync";

interface CustomMailState {
  email_account_name: string;
  email_id: string;
  domain: string;
  reply_to: string;
  email_server: string;
  incoming_port: string;
  incoming_login: string;
  incoming_password: string;
  use_ssl: boolean;
  use_imap: boolean;
  smtp_server: string;
  smtp_port: string;
  outgoing_login: string;
  outgoing_password: string;
  use_ssl_for_outgoing: boolean;
}

interface Props {
  backStep?: EmailStep;
}
interface Emits {
  (event: "update:step", step: EmailStep): void;
}

const props = withDefaults(defineProps<Props>(), { backStep: "email-add" });
const emit = defineEmits<Emits>();
const backStep = props.backStep;
const { updateOnboardingStep } = useOnboarding("helpdesk");

const state = reactive<CustomMailState>({
  email_account_name: "",
  email_id: "",
  domain: "",
  reply_to: "",
  email_server: "",
  incoming_port: "",
  incoming_login: "",
  incoming_password: "",
  use_ssl: true,
  use_imap: true,
  smtp_server: "",
  smtp_port: "",
  outgoing_login: "",
  outgoing_password: "",
  use_ssl_for_outgoing: true,
});

watch(
  () => state.domain,
  (value) => {
    if (value) syncCustomServerFromDomain(value, state);
  }
);

const createAccount = createResource({
  url: "helpdesk.api.settings.email.create_email_account",
  makeParams: (payload: Record<string, unknown>) => ({ ...payload }),
  onSuccess: () => {
    toast.success(__("Email account created"));
    emit("update:step", "email-list");
    updateOnboardingStep("setup_email_account");
    capture("email_account_created", { data: { service: "Custom" } });
  },
  onError: () =>
    toast.error(__("Failed to create email account, Invalid credentials")),
});

function save() {
  const error = validate();
  if (error) {
    toast.error(error);
    return;
  }
  createAccount.submit({ data: buildPayload() });
}

function validate(): string {
  if (!state.email_account_name) return __("Account name is required");
  if (!state.email_id) return __("Email ID is required");
  if (!validateEmailWithZod(state.email_id)) return __("Invalid email ID");
  if (state.reply_to && !validateEmailWithZod(state.reply_to))
    return __("Invalid reply-to email");
  if (!hasServerConfig())
    return __("Email Domain or manual server settings are required");
  if (!hasPassword()) return __("Password is required");
  return "";
}

function hasServerConfig(): boolean {
  if (state.domain) return true;
  return Boolean(
    state.email_server &&
      state.incoming_port &&
      state.smtp_server &&
      state.smtp_port
  );
}

function hasPassword(): boolean {
  return Boolean(state.incoming_password || state.outgoing_password);
}

function buildPayload() {
  const password = state.incoming_password || state.outgoing_password;
  return {
    email_account_name: state.email_account_name,
    email_id: state.email_id,
    service: "Custom",
    domain: state.domain,
    reply_to: state.reply_to,
    email_server: state.email_server,
    incoming_port: state.incoming_port,
    smtp_server: state.smtp_server,
    smtp_port: state.smtp_port,
    use_ssl: state.use_ssl ? 1 : 0,
    use_imap: state.use_imap ? 1 : 0,
    use_ssl_for_outgoing: state.use_ssl_for_outgoing ? 1 : 0,
    use_tls: !state.use_ssl ? 1 : 0,
    use_starttls: !state.use_ssl ? 1 : 0,
    password,
    enable_incoming: false,
    enable_outgoing: false,
    default_incoming: false,
    default_outgoing: false,
  };
}
</script>
