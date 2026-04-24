<template>
  <SettingsLayoutBase
    :description="__('Configure your Exotel settings for Helpdesk.')"
  >
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Exotel')"
          size="md"
          @click="goBack"
          class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0 !pl-0 -ml-1.5"
        />
        <Transition name="fade">
          <Badge
            v-if="isDirty.exotel"
            :label="__('Unsaved')"
            theme="orange"
            variant="subtle"
        /></Transition>
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Save')"
        theme="gray"
        variant="solid"
        @click="save"
        :disabled="!isDirty.exotel"
        :loading="exotel.save.loading"
      />
    </template>
    <template #content>
      <div class="flex flex-col h-full w-full pb-8">
        <div v-if="exotel?.doc">
          <div>
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
              <div
                class="flex flex-col gap-2"
                v-if="telephonyAgent.doc && exotel.doc?.enabled"
              >
                <FormControl
                  label="Exotel number"
                  type="text"
                  required
                  v-model="telephonyAgent.doc.exotel_number"
                />
                <ErrorMessage :message="exotelErrors.number" />
              </div>
              <div
                class="flex flex-col gap-2"
                v-if="telephonyAgent.doc && exotel.doc?.enabled"
              >
                <FormControl
                  :label="__('Personal mobile no')"
                  type="text"
                  required
                  v-model="telephonyAgent.doc.mobile_no"
                />
                <ErrorMessage :message="exotelErrors.mobileNo" />
              </div>
              <div class="flex flex-col gap-2">
                <FormControl
                  label="Account SID"
                  required
                  v-model="exotel.doc.account_sid"
                  placeholder="Account SID"
                />
                <ErrorMessage :message="exotelErrors.accountSid" />
              </div>
              <div class="flex flex-col gap-2">
                <FormControl
                  label="Webhook Verify Token"
                  required
                  v-model="exotel.doc.webhook_verify_token"
                  placeholder="Webhook Verify Token"
                />
                <ErrorMessage :message="exotelErrors.webhookVerifyToken" />
              </div>

              <div class="flex flex-col gap-2">
                <FormControl
                  label="API Key"
                  required
                  v-model="exotel.doc.api_key"
                  placeholder="API Key"
                />
                <ErrorMessage :message="exotelErrors.apiKey" />
              </div>
              <div class="flex flex-col gap-2">
                <Password
                  label="API Token"
                  required
                  v-model="exotel.doc.api_token"
                  placeholder="API Token"
                />
                <ErrorMessage :message="exotelErrors.apiToken" />
              </div>
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
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-if="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    @confirm="showConfirmDialog.onConfirm"
    @cancel="showConfirmDialog.onCancel"
  />
</template>
<script setup>
import Password from "@/components/Password.vue";
import {
  Checkbox,
  FormControl,
  createDocumentResource,
  toast,
  ErrorMessage,
  createResource,
} from "frappe-ui";
import { nextTick, ref, watch } from "vue";
import { isDocDirty, validateExotel, validateTwilio } from "./utils";
import { useAuthStore } from "@/stores/auth";
import { useTelephonyStore } from "@/stores/telephony";
import { disableSettingModalOutsideClick } from "../settingsModal";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

import { __ } from "@/translation";

const auth = useAuthStore();
const telephonyStore = useTelephonyStore();
const isDirty = ref({
  twilio: false,
  exotel: false,
  telephonyAgent: false,
});
const emit = defineEmits(["updateStep"]);

const twilioApps = ref([]);
const showConfirmDialog = ref({ show: false });

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

const goBack = () => {
  if (
    isDirty.value.twilio ||
    isDirty.value.exotel ||
    isDirty.value.telephonyAgent
  ) {
    if (!showConfirmDialog.value.show) {
      showConfirmDialog.value = {
        show: true,
        title: __("Unsaved changes"),
        message: __(
          "Are you sure you want to go back? Unsaved changes will be lost."
        ),
        onConfirm: () => {
          showConfirmDialog.value.show = false;
          emit("updateStep", "telephony-settings");
        },
        onCancel: () => {
          showConfirmDialog.value.show = false;
        },
      };
    }
    return;
  }
  emit("updateStep", "telephony-settings");
};

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
    toast.success(__("Telephony settings updated successfully."));
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
