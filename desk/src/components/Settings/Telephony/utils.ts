export const isDocDirty = (doc: any) => {
  return JSON.stringify(doc.doc) !== JSON.stringify(doc.originalDoc);
};

export const validateTwilio = (twilio, telephonyAgent, twilioErrors) => {
  if (!twilio.enabled) {
    return;
  }
  if (!twilio.account_sid) {
    twilioErrors.value.account_sid = "Account SID is required";
  } else {
    twilioErrors.value.account_sid = "";
  }
  if (!twilio.auth_token) {
    twilioErrors.value.auth_token = "Auth Token is required";
  } else {
    twilioErrors.value.auth_token = "";
  }
  if (!telephonyAgent.twilio_number) {
    twilioErrors.value.number = "Number is required";
  } else {
    twilioErrors.value.number = "";
  }
};

export const validateExotel = (exotel, telephonyAgent, exotelErrors) => {
  if (!exotel.enabled) {
    return;
  }
  if (!exotel.account_sid) {
    exotelErrors.value.account_sid = "Account SID is required";
  } else {
    exotelErrors.value.account_sid = "";
  }
  if (!exotel.webhook_verify_token) {
    exotelErrors.value.webhook_verify_token =
      "Webhook Verify Token is required";
  } else {
    exotelErrors.value.webhook_verify_token = "";
  }
  if (!exotel.subdomain) {
    exotelErrors.value.subdomain = "Subdomain is required";
  } else {
    exotelErrors.value.subdomain = "";
  }
  if (!exotel.api_key) {
    exotelErrors.value.api_key = "API Key is required";
  } else {
    exotelErrors.value.api_key = "";
  }
  if (!exotel.api_token) {
    exotelErrors.value.api_token = "API Token is required";
  } else {
    exotelErrors.value.api_token = "";
  }
  if (!telephonyAgent.exotel_number) {
    exotelErrors.value.number = "Number is required";
  } else {
    exotelErrors.value.number = "";
  }
};
