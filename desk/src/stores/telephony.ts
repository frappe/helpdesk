import { ref } from "vue";
import { call } from "frappe-ui";

let callMethod = (number?: string) => {};

export function setMakeCall(value) {
  callMethod = value;
}

export function makeCall(number) {
  callMethod(number);
}

export const callEnabled = ref(false);
export const twilioEnabled = ref(false);
export const exotelEnabled = ref(false);
export const defaultCallingMedium = ref("");

call("telephony.api.is_call_integration_enabled").then((data) => {
  twilioEnabled.value = Boolean(data.twilio_enabled);
  exotelEnabled.value = Boolean(data.exotel_enabled);
  defaultCallingMedium.value = data.default_calling_medium;
  callEnabled.value = twilioEnabled.value || exotelEnabled.value;
});

export function telephonyStore() {
  return {
    callEnabled,
    twilioEnabled,
    exotelEnabled,
    defaultCallingMedium,
    callMethod,
    setMakeCall,
    makeCall,
  };
}
