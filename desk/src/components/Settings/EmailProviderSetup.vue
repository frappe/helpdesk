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
            @click="emit('update:step', backStep)"
            class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
          />
        </div>
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="submitLabel"
        variant="solid"
        :loading="busy"
        @click="submit"
      />
    </template>
    <template #content>
      <div class="flex flex-col gap-6">
        <ProviderHeader
          v-if="selectedService"
          :name="selectedService.name"
          :icon="selectedService.icon"
          :heading="__('Set up {0}', [selectedService.name])"
          :subheading="
            __('Keep things in sync with {0}', [selectedService.name])
          "
        />

        <OAuthRedirectCallout
          v-if="isOAuthSelected"
          :redirect-uri="redirectUri"
          :service="serviceValue"
        />

        <InfoAlert
          v-else-if="selectedService"
          :text="basicInfo.text"
          :link="basicInfo.link"
        />

        <div v-if="supportsAuth" class="flex flex-col gap-2">
          <div class="text-p-sm text-ink-gray-6">
            {{ __("Authentication method") }}
          </div>
          <TabButtons :buttons="authMethodOptions" v-model="authMethod" />
        </div>

        <section class="flex flex-col gap-3">
          <h2 class="text-p-base font-medium text-ink-gray-8">
            {{ __("General settings") }}
          </h2>
          <CredentialFields
            :state="state"
            :is-o-auth="isOAuthSelected"
            :is-frappe-mail="state.service === 'Frappe Mail'"
            :account-name-placeholder="
              selectedService?.name || __('Account name')
            "
          />
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
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { capture } from "@/telemetry";
import { __ } from "@/translation";
import { EmailService, EmailStep } from "@/types";
import { Button, createResource, Switch, TabButtons, toast } from "frappe-ui";
import { useOnboarding } from "frappe-ui/frappe";
import { computed, Ref, ref, watch } from "vue";
import CredentialFields from "./Email/CredentialFields.vue";
import InfoAlert from "./Email/InfoAlert.vue";
import OAuthRedirectCallout from "./Email/OAuthRedirectCallout.vue";
import ProviderHeader from "./Email/ProviderHeader.vue";
import SettingsRow from "./Email/SettingsRow.vue";
import {
  AuthMethod,
  getAppPasswordInfo,
  getServiceByValue,
  supportsAuthToggle,
  validateInputs,
} from "./emailConfig";
import {
  buildBasicPayload,
  buildOAuthPayload,
  createProviderFormState,
  type ProviderFormState,
} from "./Email/providerForm";

interface Props {
  service: string;
  backStep?: EmailStep;
}
interface Emits {
  (event: "update:step", step: EmailStep, data?: { service?: string }): void;
}

const props = withDefaults(defineProps<Props>(), { backStep: "email-add" });
const emit = defineEmits<Emits>();
const backStep = props.backStep;
const { updateOnboardingStep } = useOnboarding("helpdesk");

const selectedService: Ref<EmailService | null> = ref(
  getServiceByValue(props.service) || null
);
const serviceValue = computed(() => selectedService.value?.value || "");
const state = createProviderFormState(serviceValue.value);

const authMethod = ref<AuthMethod>(
  supportsAuthToggle(serviceValue.value) ? "OAuth" : "Basic"
);
const authMethodOptions = [
  { label: __("OAuth"), value: "OAuth" },
  { label: __("Basic (App Password)"), value: "Basic" },
];

const supportsAuth = computed(() => supportsAuthToggle(serviceValue.value));
const isOAuthSelected = computed(
  () => supportsAuth.value && authMethod.value === "OAuth"
);

const basicInfo = computed(() => {
  const override = getAppPasswordInfo(serviceValue.value);
  if (override) return override;
  return {
    text: selectedService.value?.info || "",
    link: selectedService.value?.link || "",
  };
});

const submitLabel = computed(() => {
  if (!isOAuthSelected.value) return __("Save");
  if (serviceValue.value === "GMail") return __("Connect with Google");
  if (serviceValue.value === "Outlook.com") return __("Connect with Microsoft");
  return __("Connect");
});

const createAccount = createResource({
  url: "helpdesk.api.settings.email.create_email_account",
  makeParams: (payload: ProviderFormState) => ({ ...payload }),
  onSuccess: () => {
    toast.success(__("Email account created"));
    emit("update:step", "email-list");
    updateOnboardingStep("setup_email_account");
    capture("email_account_created", { data: { service: state.service } });
  },
  onError: () =>
    toast.error(__("Failed to create email account, Invalid credentials")),
});

const initiateOAuth = createResource({
  url: "helpdesk.api.settings.email.initiate_oauth_email",
  onSuccess: (data: { redirect_url?: string }) => {
    capture("email_account_oauth_initiated", {
      data: { service: state.service },
    });
    updateOnboardingStep("setup_email_account");
    if (data?.redirect_url) {
      window.location.href = data.redirect_url;
      return;
    }
    toast.error(__("Failed to start OAuth flow"));
  },
  onError: (err: { messages?: string[]; message?: string }) =>
    toast.error(
      err?.messages?.[0] || err?.message || __("Failed to start OAuth flow")
    ),
});

const redirectUri = ref<string | null>(null);
const fetchRedirectUri = createResource({
  url: "helpdesk.api.settings.email.get_oauth_redirect_uri",
  makeParams: (params: { service: string }) => params,
  onSuccess: (data: { redirect_uri: string }) => {
    redirectUri.value = data?.redirect_uri || null;
  },
});

watch(
  () => selectedService.value?.value,
  (name) => {
    redirectUri.value = null;
    if (selectedService.value?.oauth && name) {
      fetchRedirectUri.submit({ service: name });
    }
  },
  { immediate: true }
);

const busy = computed(() => createAccount.loading || initiateOAuth.loading);

function submit() {
  const error = validateInputs(state, state.service, false, authMethod.value);
  if (error) return toast.error(error);
  if (isOAuthSelected.value) {
    initiateOAuth.submit({ data: buildOAuthPayload(state) });
    return;
  }
  createAccount.submit({ data: buildBasicPayload(state) });
}
</script>
