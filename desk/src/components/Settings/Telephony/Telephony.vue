<template>
  <SettingsLayoutBase :description="__('Configure your telephony settings.')">
    <template #title>
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("Telephony") }}
        </h1>
        <Badge
          :class="[
            isDirty.twilio || isDirty.exotel || isDirty.telephonyAgent
              ? 'opacity-100'
              : 'opacity-0',
          ]"
          :label="__('Unsaved')"
          theme="orange"
          variant="subtle"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Save')"
        theme="gray"
        variant="solid"
        @click="save"
        :disabled="
          !isDirty.twilio && !isDirty.exotel && !isDirty.telephonyAgent
        "
        :loading="
          twilio.save.loading ||
          exotel.save.loading ||
          telephonyAgent.save.loading
        "
      />
    </template>
    <template #content>
      <div>
        <div class="text-base font-semibold text-ink-gray-8">
          {{ __("Agent settings") }}
        </div>
        <div class="text-p-xs text-ink-gray-6 mt-1">
          {{ __("Configure your agent’s telephony details.") }}
        </div>
        <div class="grid grid-cols-2 gap-4 mt-4">
          <div class="flex flex-col gap-1.5">
            <FormLabel :label="__('Default medium')" />
            <Select
              v-if="telephonyAgent.doc"
              :options="telephonyProviders"
              :modelValue="telephonyAgent.doc?.default_medium"
              @update:modelValue="telephonyAgent.doc.default_medium = $event"
            />
            <ErrorMessage
              :message="
                twilioErrors.default_medium || exotelErrors.default_medium
              "
            />
          </div>
          <div
            class="flex flex-col gap-1.5"
            v-if="telephonyAgent.doc && twilio.doc?.enabled"
          >
            <FormControl
              :label="__('Twilio number')"
              type="text"
              required
              v-model="telephonyAgent.doc.twilio_number"
            />
            <ErrorMessage :message="twilioErrors.number" />
          </div>
          <div
            class="flex flex-col gap-1.5"
            v-if="telephonyAgent.doc && exotel.doc?.enabled"
          >
            <FormControl
              :label="__('Exotel number')"
              type="text"
              required
              v-model="telephonyAgent.doc.exotel_number"
            />
            <ErrorMessage :message="exotelErrors.number" />
          </div>
          <div
            class="flex flex-col gap-1.5"
            v-if="telephonyAgent.doc && exotel.doc?.enabled"
          >
            <FormControl
              :label="__('Personal mobile no')"
              type="text"
              required
              v-model="telephonyAgent.doc.mobile_no"
              :description="__('Required for exotel integration')"
            />
            <ErrorMessage :message="exotelErrors.mobileNo" />
          </div>
        </div>
        <div class="mt-6" v-if="twilio?.doc">
          <div class="text-base font-semibold text-ink-gray-8">
            {{ __("Twilio") }}
          </div>
          <div class="mt-4">
            <div class="grid grid-cols-2 gap-4">
              <Checkbox
                :label="__('Enabled')"
                v-model="twilio.doc.enabled"
                @update:modelValue="twilio.doc.enabled = $event ? 1 : 0"
              />
              <Checkbox
                :label="__('Record Calls')"
                v-model="twilio.doc.record_calls"
                v-if="twilio.doc.enabled"
                @update:modelValue="twilio.doc.record_calls = $event ? 1 : 0"
              />
            </div>
            <div class="grid grid-cols-2 gap-4 mt-4" v-if="twilio.doc.enabled">
              <div class="flex flex-col gap-2">
                <FormControl
                  :label="__('Account SID')"
                  required
                  v-model="twilio.doc.account_sid"
                  :placeholder="__('Account SID')"
                />
                <ErrorMessage :message="twilioErrors.accountSid" />
              </div>
              <div class="flex flex-col gap-2">
                <Password
                  :label="__('Auth Token')"
                  required
                  v-model="twilio.doc.auth_token"
                  :placeholder="__('Auth Token')"
                />
                <ErrorMessage :message="twilioErrors.authToken" />
              </div>
              <FormControl
                v-if="twilio.doc.api_key"
                :label="__('API Key')"
                v-model="twilio.doc.api_key"
                disabled
              />
              <Password
                v-if="twilio.doc.api_secret"
                :label="__('API Secret')"
                v-model="twilio.doc.api_secret"
                disabled
              />
              <Autocomplete
                v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
                :label="__('TwiML App Name')"
                :model-value="twilio.doc.app_name"
                @update:modelValue="twilio.doc.app_name = $event.value"
                :options="twilioApps"
              >
                <template #footer="{ togglePopover }">
                  <Button
                    :label="__('Refresh Apps')"
                    theme="gray"
                    variant="subtle"
                    class="w-full"
                    icon-left="refresh-cw"
                    @click="refreshApps(togglePopover)"
                    :loading="twilioAppsResource.loading"
                  />
                </template>
              </Autocomplete>
              <FormControl
                v-if="twilio.doc.twiml_sid"
                :label="__('TwiML App SID')"
                v-model="twilio.doc.twiml_sid"
                disabled
              />
            </div>
          </div>
        </div>
        <div class="mt-6" v-if="exotel?.doc">
          <div class="text-base font-semibold text-ink-gray-8">
            {{ __("Exotel") }}
          </div>
          <div class="mt-4">
            <div class="grid grid-cols-2 gap-4">
              <Checkbox
                :label="__('Enabled')"
                v-model="exotel.doc.enabled"
                @update:modelValue="exotel.doc.enabled = $event ? 1 : 0"
              />
              <Checkbox
                :label="__('Record Calls')"
                v-model="exotel.doc.record_call"
                v-if="exotel.doc.enabled"
                @update:modelValue="exotel.doc.record_call = $event ? 1 : 0"
              />
            </div>
            <div class="grid grid-cols-2 gap-4 mt-4" v-if="exotel.doc.enabled">
              <div class="flex flex-col gap-2">
                <FormControl
                  :label="__('Account SID')"
                  required
                  v-model="exotel.doc.account_sid"
                  :placeholder="__('Account SID')"
                />
                <ErrorMessage :message="exotelErrors.accountSid" />
              </div>
              <div class="flex flex-col gap-2">
                <FormControl
                  :label="__('Webhook Verify Token')"
                  required
                  v-model="exotel.doc.webhook_verify_token"
                  :placeholder="__('Webhook Verify Token')"
                />
                <ErrorMessage :message="exotelErrors.webhookVerifyToken" />
              </div>

              <div class="flex flex-col gap-2">
                <FormControl
                  :label="__('API Key')"
                  required
                  v-model="exotel.doc.api_key"
                  :placeholder="__('API Key')"
                />
                <ErrorMessage :message="exotelErrors.apiKey" />
              </div>
              <div class="flex flex-col gap-2">
                <Password
                  :label="__('API Token')"
                  required
                  v-model="exotel.doc.api_token"
                  :placeholder="__('API Token')"
                />
                <ErrorMessage :message="exotelErrors.apiToken" />
              </div>
              <div class="flex flex-col gap-2">
                <FormControl
                  :label="__('Subdomain')"
                  required
                  v-model="exotel.doc.subdomain"
                  :placeholder="__('Subdomain')"
                />
                <ErrorMessage :message="exotelErrors.subdomain" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import Password from "@/components/Password.vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import {
  Button,
  Select,
  FormLabel,
  Checkbox,
  FormControl,
  createDocumentResource,
  toast,
  ErrorMessage,
  createResource,
  Badge,
  Autocomplete,
} from "frappe-ui";
import { nextTick, ref, watch } from "vue";
import { isDocDirty, validateExotel, validateTwilio } from "./utils";
import { useAuthStore } from "@/stores/auth";
import { useTelephonyStore } from "@/stores/telephony";
import { disableSettingModalOutsideClick } from "../settingsModal";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";

const auth = useAuthStore();
const telephonyStore = useTelephonyStore();
const isDirty = ref({
  twilio: false,
  exotel: false,
  telephonyAgent: false,
});
const twilioApps = ref([]);

const twilioErrors = ref({
  accountSid: "",
  authToken: "",
  number: "",
  default_medium: "",
});

const exotelErrors = ref({
  accountSid: "",
  webhookVerifyToken: "",
  subdomain: "",
  apiKey: "",
  apiToken: "",
  number: "",
  mobileNo: "",
  default_medium: "",
});

const twilio = createDocumentResource({
  doctype: "TP Twilio Settings",
  name: "TP Twilio Settings",
  cache: ["tp_twilio_settings"],
  fields: ["*"],
  auto: true,
});

const exotel = createDocumentResource({
  doctype: "TP Exotel Settings",
  name: "TP Exotel Settings",
  cache: ["tp_exotel_settings"],
  fields: ["*"],
  auto: true,
});

const telephonyAgent = createDocumentResource({
  doctype: "TP Telephony Agent",
  name: auth.user,
  cache: ["tp_telephony_agent"],
  fields: ["*"],
  auto: false,
  onError(er) {
    toast.error(er?.messages?.[0] || __("Failed to load telephony agent"));
  },
});

const twilioAppsResource = createResource({
  url: "telephony.twilio.api.fetch_applications",
  onSuccess() {
    twilio.reload();
  },
});

const telephonyProviders = [
  { label: "", value: "" },
  { label: "Twilio", value: "Twilio" },
  { label: "Exotel", value: "Exotel" },
];

async function save() {
  validateTwilio(twilio.doc, telephonyAgent.doc, twilioErrors);
  validateExotel(exotel.doc, telephonyAgent.doc, exotelErrors);
  if (Object.values(twilioErrors.value).some((v) => v)) {
    toast.error(__("Please fill all required fields for Twilio"));
    return;
  }
  if (Object.values(exotelErrors.value).some((v) => v)) {
    toast.error(__("Please fill all required fields for Exotel"));
    return;
  }

  const promises = [];

  // Temporary fix, as createDocumentResource's dirty state has bug
  if (isDirty.value.twilio) {
    promises.push(
      twilio.save.submit().catch((er) => {
        const error = __(`Twilio error: {0}`, er?.messages?.[0]);
        toast.error(error || __("Failed to save Twilio settings"));
      })
    );
  }
  if (isDirty.value.exotel) {
    promises.push(
      exotel.save.submit().catch((er) => {
        const error = __(`Exotel error: {0}`, er?.messages?.[0]);
        toast.error(error || __("Failed to save Exotel settings"));
      })
    );
  }
  if (isDirty.value.telephonyAgent) {
    if (telephonyAgent.doc.twilio_number) {
      telephonyAgent.doc.twilio = true;
    } else {
      telephonyAgent.doc.twilio = false;
    }

    if (telephonyAgent.doc.exotel_number) {
      telephonyAgent.doc.exotel = true;
    } else {
      telephonyAgent.doc.exotel = false;
    }
    promises.push(telephonyAgent.save.submit());
  }

  const results = await Promise.all(promises);

  if (!results.some((result) => result == undefined)) {
    toast.success(__("Telephony settings updated!"));
  }

  // Reload twilio to prevent "doc has been modified" error, as an application is created and doc is updated on save
  await twilio.reload();
  telephonyStore.fetchCallIntegrationStatus();
}

function refreshApps(togglePopover) {
  twilioAppsResource.submit().then(() => {
    // Close and reopen popover to fix bug where search does not work after refreshing list
    togglePopover();
    nextTick(() => {
      togglePopover();
    });
  });
}

createResource({
  url: "telephony.api.create_telephony_agent",
  auto: true,
  onSuccess() {
    telephonyAgent.get.submit();
  },
});

watch(
  () => telephonyAgent.doc,
  (newVal) => {
    isDirty.value.telephonyAgent = isDocDirty(
      newVal,
      telephonyAgent.originalDoc
    );
    if (isDirty.value.telephonyAgent) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);

watch(
  () => twilio.doc,
  (newVal) => {
    isDirty.value.twilio = isDocDirty(newVal, twilio.originalDoc);
    twilioApps.value =
      newVal.twilio_apps?.split(",").map((app) => ({
        label: app,
        value: app,
      })) || [];
    if (isDirty.value.twilio) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);

watch(
  () => exotel.doc,
  (newVal) => {
    isDirty.value.exotel = isDocDirty(newVal, exotel.originalDoc);
    if (isDirty.value.exotel) {
      disableSettingModalOutsideClick.value = true;
    } else {
      disableSettingModalOutsideClick.value = false;
    }
  },
  { deep: true }
);
</script>
