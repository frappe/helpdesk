<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-1 justify-center -ml-[16px]">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="__('Edit custom mail')"
            size="md"
            :disabled="loading"
            @click="emit('update:step', 'email-list')"
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
          :disabled="loading"
          @click="emit('update:step', 'email-list')"
        />
        <Button
          :label="__('Save')"
          variant="solid"
          :loading="loading"
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
          <FormControl
            v-model="state.password"
            :label="__('Password')"
            type="password"
            placeholder="••••••••••••"
          />
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
          v-model:password="state.password"
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
          v-model:password="state.password"
          v-model:useSsl="state.use_ssl_for_outgoing"
        />

        <section class="flex flex-col gap-4">
          <h2 class="text-p-base font-medium text-ink-gray-8">
            {{ __("Default settings") }}
          </h2>
          <SettingsRow
            :label="__('Enable Incoming')"
            :description="
              __(
                'Turn this on to automatically turn incoming emails into support tickets.'
              )
            "
          >
            <Switch v-model="state.enable_incoming" />
          </SettingsRow>
          <SettingsRow
            :label="__('Enable Outgoing')"
            :description="
              __(
                'When enabled, this account can be used to send outgoing emails.'
              )
            "
          >
            <Switch v-model="state.enable_outgoing" />
          </SettingsRow>
        </section>

        <ErrorMessage v-if="error" :message="error" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { EmailAccount, EmailStep } from "@/types";
import { validateEmailWithZod } from "@/utils";
import {
  Button,
  call,
  ErrorMessage,
  FormControl,
  Switch,
  toast,
} from "frappe-ui";
import { reactive, ref, watch } from "vue";
import CustomServerSection from "./Email/CustomServerSection.vue";
import SettingsRow from "./Email/SettingsRow.vue";
import {
  openDomainCreate,
  openDomainEdit,
  syncCustomServerFromDomain,
} from "./Email/domainSync";

interface Props {
  accountData: EmailAccount;
}
interface Emits {
  (event: "update:step", step: EmailStep): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const state = reactive({
  email_account_name: props.accountData.email_account_name || "",
  email_id: props.accountData.email_id || "",
  domain: props.accountData.domain || "",
  password: props.accountData.password || "",
  email_server: props.accountData.email_server || "",
  incoming_port: String(props.accountData.incoming_port || ""),
  incoming_login: props.accountData.login_id || "",
  smtp_server: props.accountData.smtp_server || "",
  smtp_port: String(props.accountData.smtp_port || ""),
  outgoing_login: props.accountData.login_id || "",
  use_ssl: Boolean(props.accountData.use_ssl),
  use_imap: Boolean(props.accountData.use_imap),
  use_ssl_for_outgoing: Boolean(props.accountData.use_ssl_for_outgoing),
  enable_incoming: Boolean(props.accountData.enable_incoming),
  enable_outgoing: Boolean(props.accountData.enable_outgoing),
});

const error = ref<string | undefined>();
const loading = ref(false);

watch(
  () => state.domain,
  (value) => {
    if (value && value !== props.accountData.domain) {
      syncCustomServerFromDomain(value, state);
    }
  }
);

async function save() {
  error.value = validate();
  if (error.value) {
    toast.error(error.value);
    return;
  }
  try {
    loading.value = true;
    if (props.accountData.email_account_name !== state.email_account_name) {
      await renameAccount();
    }
    await saveFields();
    toast.success(__("Email account updated successfully"));
    emit("update:step", "email-list");
  } catch (err) {
    const e = err as { message?: string; messages?: string[] };
    error.value =
      e?.messages?.[0] || e?.message || __("Failed to update email account");
  } finally {
    loading.value = false;
  }
}

function validate(): string {
  if (!state.email_account_name) return __("Account name is required");
  if (!state.email_id) return __("Email ID is required");
  if (!validateEmailWithZod(state.email_id)) return __("Invalid email ID");
  if (!state.domain && !(state.email_server && state.smtp_server))
    return __("Email Domain or manual server settings are required");
  return "";
}

async function renameAccount() {
  await call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: props.accountData.email_account_name,
    new_name: state.email_account_name,
  });
}

async function saveFields() {
  await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: state.email_account_name,
    fieldname: buildPayload(),
  });
}

function buildPayload() {
  return {
    email_id: state.email_id,
    domain: state.domain,
    email_server: state.email_server,
    incoming_port: state.incoming_port,
    smtp_server: state.smtp_server,
    smtp_port: state.smtp_port,
    use_ssl: state.use_ssl ? 1 : 0,
    use_imap: state.use_imap ? 1 : 0,
    use_ssl_for_outgoing: state.use_ssl_for_outgoing ? 1 : 0,
    enable_incoming: state.enable_incoming ? 1 : 0,
    enable_outgoing: state.enable_outgoing ? 1 : 0,
    ...(state.password ? { password: state.password } : {}),
  };
}
</script>
