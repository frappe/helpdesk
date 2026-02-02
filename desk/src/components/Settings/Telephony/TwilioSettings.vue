<template>
        
        
             <SettingsLayoutBase :description="__('Configure your Twilio settings.')">
    <template #title>
      <div class="flex items-center gap-2">
     <Button
        :icon="LucideChevronLeft"
        variant="ghost"
        @click="$emit('updateStep', 'telephony-settings')"
      />
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("Twilio") }}
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
  
          telephonyAgent.save.loading
        "
      />
    </template>
    <template #content> 
     

                <div v-if="twilio?.doc">
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
                  label="Account SID"
                  required
                  v-model="twilio.doc.account_sid"
                  placeholder="Account SID"
                />
                <ErrorMessage :message="twilioErrors.accountSid" />
              </div>
              <div class="flex flex-col gap-2">
                <Password
                  label="Auth Token"
                  required
                  v-model="twilio.doc.auth_token"
                  placeholder="Auth Token"
                />
                <ErrorMessage :message="twilioErrors.authToken" />
              </div>
              <FormControl
                v-if="twilio.doc.api_key"
                label="API Key"
                v-model="twilio.doc.api_key"
                disabled
              />
              <Password
                v-if="twilio.doc.api_secret"
                label="API Secret"
                v-model="twilio.doc.api_secret"
                disabled
              />
              <Autocomplete
                v-if="twilio.originalDoc?.account_sid && twilioApps.length > 0"
                label="TwiML App Name"
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
                label="TwiML App SID"
                v-model="twilio.doc.twiml_sid"
                disabled
              />
                   <div
            class="flex flex-col gap-1.5"
            v-if="telephonyAgent.doc && twilio.doc?.enabled"
          >
            <FormControl
              label="Twilio number"
              type="text"
              required
              v-model="telephonyAgent.doc.twilio_number"
            />
            <ErrorMessage :message="twilioErrors.number" />
          </div>
            </div>
          </div>
        </div>
    </template>
             </SettingsLayoutBase>
          
          </template>
<script setup>
import Password from "@/components/Password.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
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
import LucideChevronLeft from "~icons/lucide/chevron-left";

import { disableSettingModalOutsideClick } from "../settingsModal";
const twilioApps = ref([]);
const auth = useAuthStore();

const twilioErrors = ref({
  accountSid: "",
  authToken: "",
  number: "",
  default_medium: "",
});
const isDirty = ref({
  twilio: false,
  exotel: false,
  telephonyAgent: false,
});

const twilio = createDocumentResource({
  doctype: "TP Twilio Settings",
  name: "TP Twilio Settings",
  cache: ["tp_twilio_settings"],
  fields: ["*"],
  auto: true,
});

const twilioAppsResource = createResource({
  url: "telephony.twilio.api.fetch_applications",
  onSuccess() {
    twilio.reload();
  },
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

const emit = defineEmits(['updateStep'])
</script>
