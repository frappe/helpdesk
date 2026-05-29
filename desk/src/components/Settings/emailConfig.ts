import LogoFrappeMail from "@/assets/images/frappe-mail.svg";
import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";
import { EmailService } from "@/types";
import { __ } from "@/translation";
import { validateEmailWithZod } from "@/utils";

export type AuthMethod = "Basic" | "OAuth";

// Backend values for OAuth-capable services (match Email Account.service).
const OAUTH_SERVICE_VALUES = new Set(["GMail", "Outlook.com"]);

export function isOAuthService(serviceValue?: string): boolean {
  return Boolean(serviceValue && OAUTH_SERVICE_VALUES.has(serviceValue));
}

export const supportsAuthToggle = isOAuthService;

export const services: EmailService[] = [
  {
    name: "GMail",
    value: "GMail",
    icon: LogoGmail,
    info: __(
      "Connect with Google using OAuth. Create an OAuth Client in Google Cloud Console and paste the Client ID and Client Secret below. Read more"
    ),
    link: "https://support.google.com/cloud/answer/6158849",
    custom: false,
    oauth: true,
  },
  {
    name: "Outlook",
    value: "Outlook.com",
    icon: LogoOutlook,
    info: __(
      "Connect with Microsoft using OAuth. Register an app in Azure Portal and paste the Client ID and Client Secret below. Read more"
    ),
    link: "https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app",
    custom: false,
    oauth: true,
  },
  {
    name: "Sendgrid",
    value: "Sendgrid",
    icon: LogoSendgrid,
    info: __(
      "Setting up Sendgrid requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/",
    custom: false,
  },
  {
    name: "SparkPost",
    value: "SparkPost",
    icon: LogoSparkpost,
    info: __(
      "Setting up SparkPost requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication",
    custom: false,
  },
  {
    name: "Yahoo",
    value: "Yahoo Mail",
    icon: LogoYahoo,
    info: __(
      "Setting up Yahoo requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://help.yahoo.com/kb/SLN15241.html",
    custom: false,
  },
  {
    name: "Yandex",
    value: "Yandex.Mail",
    icon: LogoYandex,
    info: __(
      "Setting up Yandex requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://yandex.com/support/id/authorization/app-passwords.html",
    custom: false,
  },
  {
    name: "Frappe Mail",
    value: "Frappe Mail",
    icon: LogoFrappeMail,
    info: __(
      "Setting up Frappe Mail requires you to have an API key and API Secret of your email account. Read more"
    ),
    link: "https://github.com/frappe/mail",
    custom: true,
  },
  {
    name: "Custom",
    value: "Custom",
    icon: "",
    info: __("Use your own IMAP/SMTP settings. Open in Desk"),
    link: "/desk/email-account/new-email-account",
    custom: true,
  },
];

// Indexed by backend service value (what gets stored on Email Account.service).
export const emailIcon: Record<string, string> = services.reduce(
  (acc, service) => {
    acc[service.value] = service.icon;
    return acc;
  },
  {} as Record<string, string>
);

export function getServiceByValue(value?: string): EmailService | undefined {
  if (!value) return undefined;
  return services.find((s) => s.value === value);
}

const appPasswordInfo: Record<string, { text: string; link: string }> = {
  GMail: {
    text: __(
      "Setting up GMail requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://support.google.com/accounts/answer/185833",
  },
  "Outlook.com": {
    text: __(
      "Setting up Outlook requires you to enable two factor authentication and app specific passwords. Read more"
    ),
    link: "https://support.microsoft.com/account-billing/5896ed9b-4263-e681-128a-a6f2979a7944",
  },
};

export function getAppPasswordInfo(serviceValue?: string) {
  if (!serviceValue) return null;
  return appPasswordInfo[serviceValue] || null;
}

export interface EmailAccountFormState {
  email_account_name?: string;
  email_id?: string;
  password?: string;
  api_key?: string;
  api_secret?: string;
  client_id?: string;
  client_secret?: string;
  frappe_mail_site?: string;
  domain?: string;
  email_server?: string;
  incoming_port?: string | number;
  smtp_server?: string;
  smtp_port?: string | number;
}

export function validateInputs(
  state: EmailAccountFormState,
  service: string,
  allowMissingPassword = false,
  authMethod: AuthMethod = "Basic"
): string {
  if (!state.email_account_name) return __("Account name is required.");
  if (!state.email_id) return __("Email ID is required.");
  if (!validateEmailWithZod(state.email_id)) return __("Invalid email ID.");

  if (isOAuthService(service) && authMethod === "OAuth") {
    if (allowMissingPassword) return "";
    if (!state.client_id) return __("Client ID is required.");
    if (!state.client_secret) return __("Client Secret is required.");
    return "";
  }

  if (service === "Frappe Mail") {
    if (!state.api_key) return __("API Key is required.");
    if (!state.api_secret) return __("API Secret is required.");
    return "";
  }

  if (service === "Custom") return validateCustom(state, allowMissingPassword);

  if (!state.password && !allowMissingPassword) return __("Password is required.");
  return "";
}

function validateCustom(
  state: EmailAccountFormState,
  allowMissingPassword: boolean
): string {
  const hasDomain = Boolean(state.domain);
  const hasManualServers =
    state.email_server &&
    state.incoming_port &&
    state.smtp_server &&
    state.smtp_port;
  if (!hasDomain && !hasManualServers)
    return __("Email Domain or manual server settings are required.");
  if (!state.password && !allowMissingPassword)
    return __("Password is required");
  return "";
}
