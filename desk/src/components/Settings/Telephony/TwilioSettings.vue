<template>
  <SettingsLayoutBase
    :description="__('Configure your Twilio settings for Helpdesk.')"
  >
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Twilio')"
          size="md"
          @click="goBack"
          class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0 !pl-0 -ml-1.5"
        />
        <Transition name="fade">
          <Badge
            v-if="isDirty.twilio"
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
        :disabled="!isDirty.twilio"
        :loading="twilio.save.loading"
      />
    </template>
    <template #content>
      <div v-if="twilio?.doc">
        <div>
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
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import {
  Button,
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

const showConfirmDialog = ref({ show: false });

const goBack = () => {
  if (isDirty.value.twilio || isDirty.value.telephonyAgent) {
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
  if (Object.values(twilioErrors.value).some((v) => v)) {
    toast.error(__("Please fill all required fields for Twilio"));
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

  if (isDirty.value.telephonyAgent) {
    if (telephonyAgent.doc.twilio_number) {
      telephonyAgent.doc.twilio = true;
    } else {
      telephonyAgent.doc.twilio = false;
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

const emit = defineEmits(["updateStep"]);
</script>
