<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-1 justify-center -ml-[16px]">
          <Button
            variant="ghost"
            icon-left="chevron-left"
            :label="__('Account detail')"
            size="md"
            :disabled="busy"
            @click="emit('update:step', 'email-list')"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
          />
        </div>
      </div>
    </template>
    <template #header-actions>
      <div class="flex items-center gap-2">
        <Button
          v-if="isOAuthAccount && !isAuthMethodChanged"
          :label="reconnectLabel"
          variant="subtle"
          :loading="reconnectRes.loading"
          :disabled="loading"
          @click="reconnectRes.submit()"
        />
        <Button
          v-if="accountData.enable_incoming && !isAuthMethodChanged"
          :label="__('Pull Emails')"
          variant="subtle"
          :loading="loadingPull"
          :disabled="loading"
          @click="pullEmails"
        />
        <Button
          v-if="supportsAuth && isAuthMethodChanged"
          :label="
            authMethod === 'OAuth'
              ? __('Switch to OAuth')
              : __('Switch to Basic')
          "
          variant="solid"
          :loading="switchAuthRes.loading"
          :disabled="loading"
          @click="switchAuth"
        />
        <Button
          v-else
          :label="__('Save')"
          variant="solid"
          :loading="loading"
          @click="updateAccount"
        />
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-6">
        <ProviderHeader
          v-if="serviceDef"
          :name="serviceDef.name"
          :icon="serviceDef.icon"
          :heading="state.email_id"
          :subheading="__('Keep things in sync with {0}', [serviceDef.name])"
        >
          <template #suffix>
            <Badge
              v-if="isOAuthAccount"
              variant="subtle"
              :label="oauthBadgeLabel"
              :theme="oauthStatus?.connected === false ? 'orange' : 'green'"
            />
          </template>
        </ProviderHeader>

        <div v-if="supportsAuth" class="flex flex-col gap-2">
          <div class="text-p-sm text-ink-gray-6">
            {{ __("Authentication method") }}
          </div>
          <TabButtons :buttons="authMethodOptions" v-model="authMethod" />
        </div>

        <div
          v-if="supportsAuth && isAuthMethodChanged"
          class="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          <FormControl
            v-if="authMethod === 'OAuth'"
            v-model="switchState.client_id"
            :label="__('Client ID')"
            type="text"
            :placeholder="__('OAuth Client ID')"
          />
          <FormControl
            v-if="authMethod === 'OAuth'"
            v-model="switchState.client_secret"
            :label="__('Client Secret')"
            type="password"
            placeholder="••••••••••••"
          />
          <FormControl
            v-if="authMethod === 'Basic'"
            v-model="switchState.password"
            :label="__('App Password')"
            type="password"
            placeholder="••••••••••••"
          />
        </div>

        <section class="flex flex-col gap-3">
          <h2 class="text-p-base font-medium text-ink-gray-8">
            {{ __("General settings") }}
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormControl
              v-model="state.email_id"
              :label="__('Email')"
              type="email"
              placeholder="johndoe@example.com"
            />
            <FormControl
              v-if="!isOAuthAccount && currentServiceName !== 'Frappe Mail'"
              v-model="state.password"
              :label="__('Password')"
              type="password"
              placeholder="••••••••••••"
            />
            <FormControl
              v-if="currentServiceName === 'Frappe Mail'"
              v-model="state.api_key"
              :label="__('API Key')"
              type="text"
              placeholder="••••••••••••"
            />
            <FormControl
              v-if="currentServiceName === 'Frappe Mail'"
              v-model="state.api_secret"
              :label="__('API Secret')"
              type="password"
              placeholder="••••••••••••"
            />
            <FormControl
              v-model="state.email_account_name"
              :label="__('Account name')"
              type="text"
              :placeholder="__('Support / Sales')"
            />
            <FormControl
              v-if="currentServiceName === 'Frappe Mail'"
              v-model="state.frappe_mail_site"
              :label="__('Frappe Mail site')"
              type="text"
              placeholder="https://frappemail.com"
            />
          </div>
        </section>

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

        <ErrorMessage v-if="combinedError" :message="combinedError" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { EmailAccount, EmailStep } from "@/types";
import { useStorage } from "@vueuse/core";
import {
  Badge,
  Button,
  call,
  createResource,
  ErrorMessage,
  FormControl,
  Switch,
  TabButtons,
  toast,
} from "frappe-ui";
import { computed, h, onMounted, reactive, ref } from "vue";
import CircleAlert from "~icons/lucide/circle-alert";
import ProviderHeader from "./Email/ProviderHeader.vue";
import SettingsRow from "./Email/SettingsRow.vue";
import { useAuthSwitch } from "./Email/useAuthSwitch";
import {
  getServiceByValue,
  supportsAuthToggle,
  validateInputs,
} from "./emailConfig";

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
  service: props.accountData.service || "",
  email_id: props.accountData.email_id || "",
  api_key: props.accountData.api_key || "",
  api_secret: props.accountData.api_secret || "",
  password: props.accountData.password || "",
  frappe_mail_site: props.accountData.frappe_mail_site || "",
  enable_incoming: Boolean(props.accountData.enable_incoming),
  enable_outgoing: Boolean(props.accountData.enable_outgoing),
});

const error = ref<string | undefined>();
const loading = ref(false);
const loadingPull = useStorage(
  `loading-emails-${state.email_account_name}`,
  false
);

const currentServiceName = computed(() => state.service || "");
const serviceDef = computed(() => getServiceByValue(currentServiceName.value));
const isOAuthAccount = computed(
  () => props.accountData.auth_method === "OAuth"
);
const supportsAuth = computed(() =>
  supportsAuthToggle(currentServiceName.value)
);
const currentAuthMethod = computed(() =>
  props.accountData.auth_method === "OAuth" ? "OAuth" : "Basic"
);

const accountName = ref(state.email_account_name);
const {
  authMethod,
  authMethodOptions,
  switchState,
  isAuthMethodChanged,
  switchAuthRes,
  submit: switchAuth,
  error: switchError,
} = useAuthSwitch({
  emailAccountName: accountName,
  service: currentServiceName,
  currentAuthMethod,
  onSwitched: () => emit("update:step", "email-list"),
});

const oauthStatus = ref<{ connected: boolean; is_oauth: boolean } | null>(null);
const oauthStatusRes = createResource({
  url: "helpdesk.api.settings.email.get_oauth_status",
  makeParams: () => ({ email_account: state.email_account_name }),
  onSuccess: (data: { connected: boolean; is_oauth: boolean }) => {
    oauthStatus.value = data;
  },
});

const reconnectRes = createResource({
  url: "helpdesk.api.settings.email.reconnect_oauth_email",
  makeParams: () => ({ email_account: state.email_account_name }),
  onSuccess: (data: { redirect_url?: string }) => {
    if (data?.redirect_url) window.location.href = data.redirect_url;
    else error.value = __("Failed to start OAuth reconnect");
  },
  onError: (err: { messages?: string[]; message?: string }) => {
    error.value =
      err?.messages?.[0] ||
      err?.message ||
      __("Failed to start OAuth reconnect");
  },
});

onMounted(() => {
  if (isOAuthAccount.value && state.email_account_name) {
    oauthStatusRes.submit();
  }
});

const oauthBadgeLabel = computed(() => {
  if (!oauthStatus.value) return __("OAuth");
  return oauthStatus.value.connected
    ? __("Connected")
    : __("Reconnect required");
});

const reconnectLabel = computed(() =>
  oauthStatus.value && !oauthStatus.value.connected
    ? __("Reconnect")
    : __("Re-authorize")
);

const busy = computed(
  () => loading.value || switchAuthRes.loading || reconnectRes.loading
);

const combinedError = computed(() => error.value || switchError.value);

async function updateAccount() {
  error.value = validateInputs(state, currentServiceName.value, true);
  if (error.value) return;
  const nameChanged =
    props.accountData.email_account_name !== state.email_account_name;
  if (!nameChanged && !isDirty.value) {
    toast.create({
      message: __("No changes made"),
      icon: h(CircleAlert, { class: "text-ink-blue-2" }),
    });
    return;
  }
  try {
    loading.value = true;
    if (nameChanged) await renameAccount();
    if (isDirty.value) await saveFields(buildUpdatePayload());
    emit("update:step", "email-list");
    toast.success(__("Email account updated successfully"));
  } catch {
    error.value = __("Failed to update email account, Invalid credentials");
  } finally {
    loading.value = false;
  }
}

function buildUpdatePayload() {
  const base = {
    email_id: state.email_id,
    service: state.service,
    enable_incoming: state.enable_incoming,
    enable_outgoing: state.enable_outgoing,
  };
  if (isOAuthAccount.value) return base;
  if (currentServiceName.value === "Frappe Mail") {
    return {
      ...base,
      frappe_mail_site: state.frappe_mail_site,
      api_key: state.api_key,
      api_secret: state.api_secret,
    };
  }
  return { ...base, password: state.password };
}

const isDirty = computed(
  () =>
    state.service !== props.accountData.service ||
    state.email_id !== props.accountData.email_id ||
    state.api_key !== (props.accountData.api_key || "") ||
    state.api_secret !== (props.accountData.api_secret || "") ||
    state.password !== (props.accountData.password || "") ||
    state.enable_incoming !== Boolean(props.accountData.enable_incoming) ||
    state.enable_outgoing !== Boolean(props.accountData.enable_outgoing) ||
    state.frappe_mail_site !== (props.accountData.frappe_mail_site || "")
);

async function renameAccount() {
  await call("frappe.client.rename_doc", {
    doctype: "Email Account",
    old_name: props.accountData.email_account_name,
    new_name: state.email_account_name,
  });
  accountName.value = state.email_account_name;
}

async function saveFields(values: Record<string, unknown>) {
  await call("frappe.client.set_value", {
    doctype: "Email Account",
    name: state.email_account_name,
    fieldname: values,
  });
}

function pullEmails() {
  loadingPull.value = true;
  toast.create({
    message: __("Pulling emails, this may take a few minutes."),
    icon: h(CircleAlert, { class: "text-ink-blue-2" }),
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
</script>
