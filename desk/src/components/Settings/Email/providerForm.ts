import { reactive } from "vue";

export interface ProviderFormState {
  service: string;
  email_account_name: string;
  email_id: string;
  password: string;
  api_key: string;
  api_secret: string;
  client_id: string;
  client_secret: string;
  frappe_mail_site: string;
  enable_incoming: boolean;
  enable_outgoing: boolean;
}

export function createProviderFormState(service: string): ProviderFormState {
  return reactive<ProviderFormState>({
    service,
    email_account_name: "",
    email_id: "",
    password: "",
    api_key: "",
    api_secret: "",
    client_id: "",
    client_secret: "",
    frappe_mail_site: "",
    enable_incoming: false,
    enable_outgoing: false,
  });
}

interface CommonPayload {
  email_account_name: string;
  email_id: string;
  service: string;
  enable_incoming: boolean;
  enable_outgoing: boolean;
  default_incoming: false;
  default_outgoing: false;
}

function buildCommonPayload(state: ProviderFormState): CommonPayload {
  return {
    email_account_name: state.email_account_name,
    email_id: state.email_id,
    service: state.service,
    enable_incoming: state.enable_incoming,
    enable_outgoing: state.enable_outgoing,
    default_incoming: false,
    default_outgoing: false,
  };
}

export function buildOAuthPayload(state: ProviderFormState) {
  return {
    ...buildCommonPayload(state),
    client_id: state.client_id,
    client_secret: state.client_secret,
  };
}

export function buildBasicPayload(state: ProviderFormState) {
  if (state.service === "Frappe Mail") {
    return {
      ...buildCommonPayload(state),
      frappe_mail_site: state.frappe_mail_site,
      api_key: state.api_key,
      api_secret: state.api_secret,
    };
  }
  return {
    ...buildCommonPayload(state),
    password: state.password,
  };
}
