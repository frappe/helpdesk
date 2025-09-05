export const isDocDirty = (doc: any, originalDoc: any) => {
  return JSON.stringify(doc) !== JSON.stringify(originalDoc);
};

export const validateTwilio = (twilio, telephonyAgent, twilioErrors) => {
  if (telephonyAgent.default_medium === "Twilio" && !twilio.enabled) {
    twilioErrors.value.default_medium =
      "Enable Twilio to set it as default medium";
  } else {
    twilioErrors.value.default_medium = "";
  }

  if (!twilio.enabled) {
    return;
  }

  if (!twilio.account_sid) {
    twilioErrors.value.accountSid = "Account SID is required";
  } else {
    twilioErrors.value.accountSid = "";
  }

  if (!twilio.auth_token) {
    twilioErrors.value.authToken = "Auth Token is required";
  } else {
    twilioErrors.value.authToken = "";
  }

  if (!telephonyAgent.twilio_number) {
    twilioErrors.value.number = "Number is required";
  } else if (!validatePhone(telephonyAgent.twilio_number)) {
    twilioErrors.value.number = "Please enter a valid phone number";
  } else {
    twilioErrors.value.number = "";
  }
};

export const validateExotel = (exotel, telephonyAgent, exotelErrors) => {
  if (telephonyAgent.default_medium === "Exotel" && !exotel.enabled) {
    exotelErrors.value.default_medium =
      "Enable Exotel to set it as default medium";
  } else {
    exotelErrors.value.default_medium = "";
  }

  if (!exotel.enabled) {
    return;
  }

  if (!exotel.account_sid) {
    exotelErrors.value.accountSid = "Account SID is required";
  } else {
    exotelErrors.value.accountSid = "";
  }

  if (!exotel.webhook_verify_token) {
    exotelErrors.value.webhookVerifyToken = "Webhook Verify Token is required";
  } else {
    exotelErrors.value.webhookVerifyToken = "";
  }

  if (!exotel.subdomain) {
    exotelErrors.value.subdomain = "Subdomain is required";
  } else {
    exotelErrors.value.subdomain = "";
  }

  if (!exotel.api_key) {
    exotelErrors.value.apiKey = "API Key is required";
  } else {
    exotelErrors.value.apiKey = "";
  }

  if (!exotel.api_token) {
    exotelErrors.value.apiToken = "API Token is required";
  } else {
    exotelErrors.value.apiToken = "";
  }

  if (!telephonyAgent.exotel_number) {
    exotelErrors.value.number = "Number is required";
  } else if (!validatePhone(telephonyAgent.exotel_number)) {
    exotelErrors.value.number = "Please enter a valid phone number";
  } else {
    exotelErrors.value.number = "";
  }

  if (!telephonyAgent.mobile_no) {
    exotelErrors.value.mobileNo = "Personal number is required";
  } else if (!validatePhone(telephonyAgent.mobile_no)) {
    exotelErrors.value.mobileNo = "Please enter a valid phone number";
  } else {
    exotelErrors.value.mobileNo = "";
  }
};

const validatePhone = (number: string) => {
  return /^\+?\d{8,15}$/.test(number);
};
