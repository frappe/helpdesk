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
            You can change the default calling medium from the settings
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
import { telephonyStore } from "@/stores/telephony";

const { defaultCallingMedium, exotelEnabled, setMakeCall, twilioEnabled } =
  telephonyStore();

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

function makeCall(number) {
  if (
    twilioEnabled.value &&
    exotelEnabled.value &&
    !defaultCallingMedium.value
  ) {
    mobileNumber.value = number;
    show.value = true;
    return;
  }

  callMedium.value = twilioEnabled.value ? "Twilio" : "Exotel";
  if (defaultCallingMedium.value) {
    callMedium.value = defaultCallingMedium.value;
  }

  mobileNumber.value = number;
  makeCallUsing();
}

function makeCallUsing() {
  if (isDefaultMedium.value && callMedium.value) {
    setDefaultCallingMedium();
  }

  if (callMedium.value === "Twilio") {
    twilio.value.makeOutgoingCall(mobileNumber.value);
  }

  if (callMedium.value === "Exotel") {
    exotel.value.makeOutgoingCall(mobileNumber.value);
  }
  show.value = false;
}

async function setDefaultCallingMedium() {
  await call("telephony.api.set_default_calling_medium", {
    medium: callMedium.value,
  });

  defaultCallingMedium.value = callMedium.value;
  toast.success(
    `Default calling medium set successfully to ${callMedium.value}`
  );
}

watch(
  [twilioEnabled, exotelEnabled],
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
        setMakeCall(makeCall);
      }
    }),
  { immediate: true }
);
</script>
