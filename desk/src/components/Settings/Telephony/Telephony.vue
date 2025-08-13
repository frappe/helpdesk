<template>
  <div class="px-10 py-8">
    <SettingsLayoutHeader
      title="Telephony"
      description="Configure your telephony settings."
    >
      <template #actions>
        <Button
          label="Save"
          theme="gray"
          variant="solid"
          @click="save"
          :loading="
            twilio.save.loading ||
            exotel.save.loading ||
            telephonyAgent.save.loading
          "
          :disabled="
            twilio.save.loading ||
            exotel.save.loading ||
            telephonyAgent.save.loading
          "
        />
      </template>
    </SettingsLayoutHeader>
  </div>
  <div class="px-10 pb-8 overflow-y-auto">
    <div class="text-base font-semibold text-ink-gray-8">
      Logged in user settings
    </div>
    <div class="grid grid-cols-2 gap-2 mt-4">
      <div class="flex flex-col gap-1.5">
        <FormLabel label="Default medium" />
        <Select
          v-if="telephonyAgent.doc"
          :options="telephonyProviders"
          :modelValue="telephonyAgent.doc?.default_medium"
          @update:modelValue="telephonyAgent.doc.default_medium = $event"
        />
      </div>
    </div>
    <div class="grid grid-cols-2 gap-2 mt-4">
      <div
        class="flex flex-col gap-1.5"
        v-if="telephonyAgent.doc && twilio.doc.enabled"
      >
        <FormControl
          label="Twilio number"
          required
          v-model="telephonyAgent.doc.twilio_number"
        />
        <ErrorMessage :message="twilioErrors.number" />
      </div>
      <div
        class="flex flex-col gap-1.5"
        v-if="telephonyAgent.doc && exotel.doc.enabled"
      >
        <FormControl
          label="Exotel number"
          required
          v-model="telephonyAgent.doc.exotel_number"
        />
        <ErrorMessage :message="exotelErrors.number" />
      </div>
    </div>
    <div class="mt-6" v-if="twilio?.doc">
      <div class="text-base font-semibold text-ink-gray-8">Twilio</div>
      <div class="mt-4">
        <div class="grid grid-cols-2 gap-2">
          <Checkbox label="Enabled" v-model="twilio.doc.enabled" />
          <Checkbox
            label="Record Calls"
            v-model="twilio.doc.record_calls"
            v-if="twilio.doc.enabled"
          />
        </div>

        <div class="grid grid-cols-2 gap-2 mt-4" v-if="twilio.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="Account SID"
              required
              v-model="twilio.doc.account_sid"
              placeholder="Account SID"
            />
            <ErrorMessage :message="twilioErrors.account_sid" />
          </div>
          <div class="flex flex-col gap-2">
            <Password
              label="Auth Token"
              required
              v-model="twilio.doc.auth_token"
              placeholder="Auth Token"
            />
            <ErrorMessage :message="twilioErrors.auth_token" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4" v-if="twilio.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="API Key"
              v-model="twilio.doc.api_key"
              disabled
            />
          </div>
          <div class="flex flex-col gap-2">
            <Password
              label="API Secret"
              v-model="twilio.doc.api_secret"
              disabled
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4" v-if="twilio.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="TwiML SID"
              v-model="twilio.doc.twiml_sid"
              disabled
            />
          </div>
        </div>
      </div>
    </div>
    <div class="mt-6" v-if="exotel?.doc">
      <div class="text-base font-semibold text-ink-gray-8">Exotel</div>
      <div class="mt-4">
        <div class="grid grid-cols-2 gap-2">
          <Checkbox label="Enabled" v-model="exotel.doc.enabled" />
          <Checkbox
            label="Record Calls"
            v-model="exotel.doc.record_call"
            v-if="exotel.doc.enabled"
          />
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4" v-if="exotel.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="Account SID"
              required
              v-model="exotel.doc.account_sid"
              placeholder="Account SID"
            />
            <ErrorMessage :message="exotelErrors.account_sid" />
          </div>
          <div class="flex flex-col gap-2">
            <Password
              label="Webhook Verify Token"
              required
              v-model="exotel.doc.webhook_verify_token"
              placeholder="Webhook Verify Token"
            />
            <ErrorMessage :message="exotelErrors.webhook_verify_token" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4" v-if="exotel.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="Subdomain"
              required
              v-model="exotel.doc.subdomain"
              placeholder="Subdomain"
            />
            <ErrorMessage :message="exotelErrors.subdomain" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mt-4" v-if="exotel.doc.enabled">
          <div class="flex flex-col gap-2">
            <FormControl
              label="API Key"
              required
              v-model="exotel.doc.api_key"
              placeholder="API Key"
            />
            <ErrorMessage :message="exotelErrors.api_key" />
          </div>
          <div class="flex flex-col gap-2">
            <Password
              label="API Token"
              required
              v-model="exotel.doc.api_token"
              placeholder="API Token"
            />
            <ErrorMessage :message="exotelErrors.api_token" />
          </div>
        </div>
      </div>
    </div>
  </div>
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
} from "frappe-ui";
import { ref } from "vue";
import { useUserStore } from "@/stores/user";
import { isDocDirty, validateExotel, validateTwilio } from "./utils";

const { getUser } = useUserStore();

const twilioErrors = ref({
  account_sid: "",
  auth_token: "",
  number: "",
});

const exotelErrors = ref({
  account_sid: "",
  webhook_verify_token: "",
  subdomain: "",
  api_key: "",
  api_token: "",
  number: "",
});

const twilio = createDocumentResource({
  doctype: "TF Twilio Settings",
  name: "TF Twilio Settings",
  cache: ["tf_twilio_settings"],
  fields: ["*"],
  auto: true,
});

const exotel = createDocumentResource({
  doctype: "TF Exotel Settings",
  name: "TF Exotel Settings",
  cache: ["tf_exotel_settings"],
  fields: ["*"],
  auto: true,
});

const telephonyAgent = createDocumentResource({
  doctype: "TF Telephony Agent",
  name: getUser().email,
  cache: ["tf_telephony_agent"],
  fields: ["*"],
  auto: false,
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
    toast.error("Please fill all required fields for Twilio");
    return;
  }
  if (Object.values(exotelErrors.value).some((v) => v)) {
    toast.error("Please fill all required fields for Exotel");
    return;
  }

  const promises = [];

  // Temporary fix, as createDocumentResource's dirty state has bug
  if (isDocDirty(twilio)) {
    promises.push(twilio.save.submit());
  }
  if (isDocDirty(exotel)) {
    promises.push(exotel.save.submit());
  }
  if (isDocDirty(telephonyAgent)) {
    promises.push(telephonyAgent.save.submit());
  }

  await Promise.all(promises);
  toast.success("Telephony settings updated!");
}

createResource({
  url: "telephony.api.create_telephony_agent",
  auto: true,
  onSuccess() {
    telephonyAgent.get.submit();
  },
});
</script>
