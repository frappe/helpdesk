<template>
  <SettingsLayoutBase :description="__('Configure your telephony settings.')">
    <template #title>
      <div class="flex items-center gap-2 h-6">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("Telephony") }}
        </h1>
        <Transition name="fade">
          <Badge
            v-if="isDirty.twilio || isDirty.exotel || isDirty.telephonyAgent"
            :label="__('Unsaved')"
            theme="orange"
            variant="subtle"
        /></Transition>
      </div>
    </template>
    <template #header-actions>
      <Transition name="fade">
        <div v-if="isDirty.twilio || isDirty.exotel || isDirty.telephonyAgent">
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
        </div>
      </Transition>
    </template>
    <template #content>
      <div class="-ml-2 grow">
        <div class="flex-1 flex flex-col">
          <!-- General -->
          <div
            class="flex items-center justify-between gap-8 py-3 hover:bg-gray-50 rounded px-2"
          >
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __("Default medium") }}
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __("Default calling medium for logged in user") }}
              </div>
            </div>
            <div class="flex items-center gap-2">
              <!-- <Select
                v-if="telephonyAgent.doc"
                :options="telephonyProviders"
                :modelValue="telephonyAgent.doc?.default_medium"
                @update:modelValue="telephonyAgent.doc.default_medium = $event"
              /> -->
              <SelectDropdown
                :options="telephonyProviders"
                :modelValue="telephonyAgent.doc?.default_medium"
                @update:modelValue="telephonyAgent.doc.default_medium = $event"
                :defaultValue="telephonyAgent.originalDoc?.default_medium"
                placement="bottom-start"
              />
            </div>
          </div>
          <div class="h-px border-t mx-2 border-outline-gray-modals" />

          <div
            class="flex items-center justify-between py-3 cursor-pointer rounded hover:bg-gray-50 px-2"
            @click="emit('updateStep', 'twilio-settings')"
          >
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __("Twilio") }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{
                  __(
                    "Configure your Twilio telephony integration settings here"
                  )
                }}
              </div>
            </div>
            <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
          </div>

          <div class="h-px border-t mx-2 border-outline-gray-modals" />

          <div
            class="flex items-center justify-between py-3 cursor-pointer rounded hover:bg-gray-50 px-2"
            @click="emit('updateStep', 'exotel-settings')"
          >
            <div class="flex flex-col">
              <div class="text-p-base font-medium text-ink-gray-7 truncate">
                {{ __("Exotel") }}
              </div>
              <div class="text-p-sm text-ink-gray-5 truncate">
                {{
                  __(
                    "Configure your Exotel telephony integration settings here"
                  )
                }}
              </div>
            </div>
            <FeatherIcon name="chevron-right" class="size-4 text-ink-gray-5" />
          </div>
        </div>
        <ErrorMessage :message="error" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import Password from "@/components/Password.vue";
import SettingsLayoutHeader from "../SettingsLayoutHeader.vue";
import {
  Button,
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
import SelectDropdown from "@/components/SelectDropdown.vue";
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
const emit = defineEmits(["updateStep"]);

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
  { label: "Twilio", value: "Twilio" },
  { label: "Exotel", value: "Exotel" },
];

async function save() {
  validateTwilio(twilio.doc, telephonyAgent.doc, twilioErrors);
  validateExotel(exotel.doc, telephonyAgent.doc, exotelErrors);
  if (Object.values(twilioErrors.value).some((v) => v)) {
    toast.error(__("Please configure your Twilio settings correctly"));
    return;
  }
  if (Object.values(exotelErrors.value).some((v) => v)) {
    toast.error(__("Please configure your Exotel settings correctly"));
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
