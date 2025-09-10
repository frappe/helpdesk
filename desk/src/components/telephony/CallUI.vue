<template>
  <TwilioCallUI ref="twilio" />
  <ExotelCallUI ref="exotel" />
  <Dialog
    v-model="show"
    :options="{
      title: 'Make call',
      actions: [
        {
          label: `Call using ${callMedium}`,
          variant: 'solid',
          onClick: makeCallUsing,
        },
      ],
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl type="text" v-model="mobileNumber" label="Mobile Number" />
        <FormControl
          type="select"
          v-model="callMedium"
          :label="'Calling Medium'"
          :options="['Twilio', 'Exotel']"
        />
        <div class="flex flex-col gap-1">
          <FormControl
            type="checkbox"
            v-model="isDefaultMedium"
            :label="`Make ${callMedium} as default calling medium`"
          />

          <div v-if="isDefaultMedium" class="text-sm text-ink-gray-4">
            {{
              __("You can change the default calling medium from the settings")
            }}
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup lang="ts">
import { FormControl, call, toast } from "frappe-ui";
import { nextTick, ref, watch } from "vue";
import TwilioCallUI from "./TwilioCallUI.vue";
import ExotelCallUI from "./ExotelCallUI.vue";
import { useTelephonyStore } from "@/stores/telephony";
import { storeToRefs } from "pinia";

const telephonyStore = useTelephonyStore();
const { defaultCallingMedium, isExotelEnabled, isTwilioEnabled } =
  storeToRefs(telephonyStore);

const twilio = ref(null);
const exotel = ref(null);

const callMedium = ref("Twilio");
const isDefaultMedium = ref(false);

const show = ref(false);
const mobileNumber = ref("");

const props = defineProps({
  userEmail: {
    type: String,
    default: "",
  },
});

function makeCall({ number, doctype, docname }) {
  telephonyStore.setLinkDoc({
    docname,
    doctype,
  });
  if (
    (isTwilioEnabled.value &&
      isExotelEnabled.value &&
      !defaultCallingMedium.value) ||
    !number
  ) {
    mobileNumber.value = number;
    show.value = true;
    return;
  }

  callMedium.value = isTwilioEnabled.value ? "Twilio" : "Exotel";
  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value;
  }

  mobileNumber.value = number;
  makeCallUsing();
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setCallingMedium();
    isDefaultMedium.value = false;
  }

  if (callMedium.value === "Twilio") {
    twilio.value.makeOutgoingCall(mobileNumber.value);
  }

  if (callMedium.value === "Exotel") {
    exotel.value.makeOutgoingCall(mobileNumber.value);
  }
  show.value = false;
}

async function setCallingMedium() {
  await call("telephony.api.set_default_calling_medium", {
    medium: callMedium.value,
  });

  telephonyStore.setDefaultCallingMedium(callMedium.value);
  telephonyStore.fetchCallIntegrationStatus();
  toast.success(
    `Default calling medium set successfully to ${callMedium.value}`
  );
}

watch(
  [isTwilioEnabled, isExotelEnabled],
  ([twilioValue, exotelValue]) =>
    nextTick(() => {
      if (twilioValue) {
        twilio.value.setup();
        callMedium.value = "Twilio";
      }

      if (exotelValue) {
        exotel.value.setup(props.userEmail);
        callMedium.value = "Exotel";
      }

      if (twilioValue || exotelValue) {
        callMedium.value = "Twilio";
        telephonyStore.setMakeCall(makeCall);
      }
    }),
  { immediate: true }
);
</script>
