import { defineStore } from "pinia";
import { call } from "frappe-ui";

export const useTelephonyStore = defineStore("telephony", {
  state: () => ({
    isCallingEnabled: false,
    isTwilioEnabled: false,
    isExotelEnabled: false,
    defaultCallingMedium: "",
    callMethod: (number?: string) => {},
  }),
  actions: {
    setMakeCall(value: (number?: string) => void) {
      this.callMethod = value;
    },
    setDefaultCallingMedium(value: string) {
      this.defaultCallingMedium = value;
    },
    makeCall(number: string) {
      this.callMethod(number);
    },
    setIsCallingEnabled(value: boolean) {
      this.isCallingEnabled = value;
    },
    async fetchCallIntegrationStatus() {
      try {
        const data = await call("telephony.api.is_call_integration_enabled");
        this.isTwilioEnabled = Boolean(data.twilio_enabled);
        this.isExotelEnabled = Boolean(data.exotel_enabled);
        this.defaultCallingMedium = data.default_calling_medium;
        this.isCallingEnabled = this.isTwilioEnabled || this.isExotelEnabled;
      } catch (error) {
        console.error("Failed to fetch call integration status:", error);
      }
    },
  },
});
