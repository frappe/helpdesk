import LogoFrappeMail from "@/assets/images/frappe-mail.svg";
import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";
import { EmailAccountFormState, EmailService, EmailServiceName, RenderField } from "@/types";
import { validateEmailWithZod } from "@/utils";
import { __ } from "@/translation";

const fixedFields: RenderField[] = [
  {
    label: __("Account name"),
    name: "email_account_name",
    type: "text",
    placeholder: __("Support / Sales"),
  },
  {
    label: __("Email ID"),
    name: "email_id",
    type: "email",
    placeholder: __("johndoe@example.com"),
  },
];

export const incomingOutgoingFields: RenderField[] = [
  {
    label: __("Enable Incoming"),
    name: "enable_incoming",
    type: "checkbox",
    description: __(
      "If enabled, tickets can be created from the incoming emails on this account."
    ),
  },
  {
    label: __("Enable Outgoing"),
    name: "enable_outgoing",
    type: "checkbox",
    description: __(
      "If enabled, outgoing emails can be sent from this account."
    ),
  },
  {
    label: __("Default Incoming"),
    name: "default_incoming",
    type: "checkbox",
    description: __(
      "If enabled, all replies to your company (eg: replies@yourcompany.com) will come to this account. Note: Only one account can be default incoming."
    ),
  },
  {
    label: __("Default Outgoing"),
    name: "default_outgoing",
    type: "checkbox",
    description: __(
      "If enabled, all outgoing emails will be sent from this account. Note: Only one account can be default outgoing."
    ),
  },
];

export const popularProviderFields = [
  ...fixedFields,
  {
    label: __("Password"),
    name: "password",
    type: "password",
    placeholder: "********",
  },
];

export const frappeMailFields = [
  ...fixedFields,
  {
    label: __("Frappe Mail site"),
    name: "frappe_mail_site",
    type: "text",
    placeholder: "https://frappemail.com",
  },
  {
    label: __("API Key"),
    name: "api_key",
    type: "text",
    placeholder: "********",
  },
  {
    label: __("API Secret"),
    name: "api_secret",
    type: "password",
    placeholder: "********",
  },
];

export const customProviderTopFields = [
  ...fixedFields,
  {
    label: __("Password"),
    name: "password",
    type: "password",
    placeholder: "********",
  },
  {
    label: __("Email Domain"),
    name: "domain",
    type: "text",
    placeholder: __("example.com"),
  },
];

export const customIncomingFields = [
  {
    label: __("Incoming Server (IMAP/POP)"),
    name: "email_server",
    type: "text",
    placeholder: __("imap.example.com"),
  },
  {
    label: __("Incoming Port"),
    name: "incoming_port",
    type: "text",
    placeholder: "993",
  },
  {
    label: __("Use SSL for Incoming"),
    name: "use_ssl",
    type: "checkbox",
    placeholder: "",
  },
  {
    label: __("Use TLS for Incoming"),
    name: "use_starttls",
    type: "checkbox",
    placeholder: "",
  },
];

export const customOutgoingFields = [
  {
    label: __("Outgoing Server (SMTP)"),
    name: "smtp_server",
    type: "text",
    placeholder: "smtp.example.com",
  },
  {
    label: __("Outgoing Port"),
    name: "smtp_port",
    type: "text",
    placeholder: "587",
  },
  {
    label: __("Use SSL for Outgoing"),
    name: "use_ssl_for_outgoing",
    type: "checkbox",
    placeholder: "",
  },
  {
    label: __("Use TLS for Outgoing"),
    name: "use_tls",
    type: "checkbox",
    placeholder: "",
  },
];

export const customProviderFields = customProviderTopFields;

export const services: EmailService[] = [
  {
    name: "GMail",
    icon: LogoGmail,
    info: __(`Setting up GMail requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://support.google.com/accounts/answer/185833",
    custom: false,
  },
  {
    name: "Outlook",
    icon: LogoOutlook,
    info: __(`Setting up Outlook requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944",
    custom: false,
  },
  {
    name: "Sendgrid",
    icon: LogoSendgrid,
    info: __(`Setting up Sendgrid requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/",
    custom: false,
  },
  {
    name: "SparkPost",
    icon: LogoSparkpost,
    info: __(`Setting up SparkPost requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication",
    custom: false,
  },
  {
    name: "Yahoo",
    icon: LogoYahoo,
    info: __(`Setting up Yahoo requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://help.yahoo.com/kb/SLN15241.html",
    custom: false,
  },
  {
    name: "Yandex",
    icon: LogoYandex,
    info: __(`Setting up Yandex requires you to enable two factor authentication
		  and app specific passwords. Read more`),
    link: "https://yandex.com/support/id/authorization/app-passwords.html",
    custom: false,
  },
  {
    name: "Frappe Mail",
    icon: LogoFrappeMail,
    info: __(
      `Setting up Frappe Mail requires you to have an API key and API Secret of your email account. Read more`
    ),
    link: "https://github.com/frappe/mail",
    custom: true,
  },
  {
    name: "Custom",
    icon: "",
    info: __(`Use your own IMAP/SMTP settings. Open in Desk`),
    link: "/desk/email-account/new-email-account",
    custom: true,
  },
];

export const emailIcon: Record<EmailServiceName, string> = {
  GMail: LogoGmail,
  Outlook: LogoOutlook,
  Sendgrid: LogoSendgrid,
  SparkPost: LogoSparkpost,
  Yahoo: LogoYahoo,
  Yandex: LogoYandex,
  "Frappe Mail": LogoFrappeMail,
  Custom: "",
};

export function validateInputs(
  state: EmailAccountFormState,
  service: string,
  allowMissingPassword = false
) {
  if (!state.email_account_name) {
    return __("Account name is required");
  }
  if (!state.email_id) {
    return __("Email ID is required");
  }
  const validEmail = validateEmailWithZod(state.email_id);
  if (!validEmail) {
    return __("Invalid email ID");
  }
  if (service === "Frappe Mail") {
    if (!state.api_key) {
      return __("API Key is required");
    }
    if (!state.api_secret) {
      return __("API Secret is required");
    }
    return "";
  }
  if (service === "Custom") {
    const hasDomain = Boolean(state.domain);
    const hasManualServers =
      state.email_server &&
      state.incoming_port &&
      state.smtp_server &&
      state.smtp_port;
    if (!hasDomain && !hasManualServers) {
      return __("Email Domain or manual server settings are required");
    }
    if (!state.password && !allowMissingPassword) {
      return __("Password is required");
    }
    return "";
  }
  if (!state.password && !allowMissingPassword) {
    return __("Password is required");
  }
  return "";
}
