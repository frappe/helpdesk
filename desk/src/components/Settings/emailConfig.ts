import LogoGmail from "@/assets/images/gmail.png";
import LogoOutlook from "@/assets/images/outlook.png";
import LogoSendgrid from "@/assets/images/sendgrid.png";
import LogoSparkpost from "@/assets/images/sparkpost.webp";
import LogoYahoo from "@/assets/images/yahoo.png";
import LogoYandex from "@/assets/images/yandex.png";
import LogoFrappeMail from "@/assets/images/frappe-mail.svg";
import { RenderField, EmailService } from "@/types";
import { validateEmailWithZod } from "@/utils";

type EmailAccountFormState = {
  email_account_name?: string;
  email_id?: string;
  service?: string;
  password?: string;
  api_key?: string;
  api_secret?: string;
  frappe_mail_site?: string;
  domain?: string;
  email_server?: string;
  incoming_port?: string | number;
  smtp_server?: string;
  smtp_port?: string | number;
  use_ssl?: boolean | number;
  use_starttls?: boolean | number;
  use_tls?: boolean | number;
  use_ssl_for_outgoing?: boolean | number;
  validate_ssl_certificate?: boolean | number;
  validate_ssl_certificate_for_outgoing?: boolean | number;
  attachment_limit?: string | number;
  append_emails_to_sent_folder?: boolean | number;
  sent_folder_name?: string;
};

const fixedFields: RenderField[] = [
  {
    label: "Account Name",
    name: "email_account_name",
    type: "text",
    placeholder: "Support / Sales",
  },
  {
    label: "Email ID",
    name: "email_id",
    type: "email",
    placeholder: "johndoe@example.com",
  },
];

export const incomingOutgoingFields: RenderField[] = [
  {
    label: "Enable Incoming",
    name: "enable_incoming",
    type: "checkbox",
    description:
      "If enabled, tickets can be created from the incoming emails on this account.",
  },
  {
    label: "Enable Outgoing",
    name: "enable_outgoing",
    type: "checkbox",
    description: "If enabled, outgoing emails can be sent from this account.",
  },
  {
    label: "Default Incoming",
    name: "default_incoming",
    type: "checkbox",
    description:
      "If enabled, all replies to your company (eg: replies@yourcomany.com) will come to this account. Note: Only one account can be default incoming.",
  },
  {
    label: "Default Outgoing",
    name: "default_outgoing",
    type: "checkbox",
    description:
      "If enabled, all outgoing emails will be sent from this account. Note: Only one account can be default outgoing.",
  },
];

export const popularProviderFields = [
  ...fixedFields,
  {
    label: "Password",
    name: "password",
    type: "password",
    placeholder: "********",
  },
];

export const frappeMailFields = [
  ...fixedFields,
  {
    label: "Frappe Mail Site",
    name: "frappe_mail_site",
    type: "text",
    placeholder: "https://frappemail.com",
  },
  {
    label: "API Key",
    name: "api_key",
    type: "text",
    placeholder: "********",
  },
  {
    label: "API Secret",
    name: "api_secret",
    type: "password",
    placeholder: "********",
  },
];

export const customProviderTopFields = [
  ...fixedFields,
  {
    label: "Password",
    name: "password",
    type: "password",
    placeholder: "********",
  },
  {
    label: "Email Domain",
    name: "domain",
    type: "text",
    placeholder: "example.com",
  },
];

export const customIncomingFields = [
  {
    label: "Incoming Server (IMAP/POP)",
    name: "email_server",
    type: "text",
    placeholder: "imap.example.com",
  },
  {
    label: "Incoming Port",
    name: "incoming_port",
    type: "text",
    placeholder: "993",
  },
  {
    label: "Use SSL for Incoming",
    name: "use_ssl",
    type: "checkbox",
    placeholder: "",
  },
  {
    label: "Use TLS for Incoming",
    name: "use_starttls",
    type: "checkbox",
    placeholder: "",
  },
];

export const customOutgoingFields = [
  {
    label: "Outgoing Server (SMTP)",
    name: "smtp_server",
    type: "text",
    placeholder: "smtp.example.com",
  },
  {
    label: "Outgoing Port",
    name: "smtp_port",
    type: "text",
    placeholder: "587",
  },
  {
    label: "Use SSL for Outgoing",
    name: "use_ssl_for_outgoing",
    type: "checkbox",
    placeholder: "",
  },
  {
    label: "Use TLS for Outgoing",
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
    info: `Setting up GMail requires you to enable two factor authentication
		  and app specific passwords. Read more`,
    link: "https://support.google.com/accounts/answer/185833",
    custom: false,
  },
  {
    name: "Outlook",
    icon: LogoOutlook,
    info: `Setting up Outlook requires you to enable two factor authentication
		  and app specific passwords. Read more`,
    link: "https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944",
    custom: false,
  },
  {
    name: "Sendgrid",
    icon: LogoSendgrid,
    info: `Setting up Sendgrid requires you to enable two factor authentication
		  and app specific passwords. Read more `,
    link: "https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/",
    custom: false,
  },
  {
    name: "SparkPost",
    icon: LogoSparkpost,
    info: `Setting up SparkPost requires you to enable two factor authentication
		  and app specific passwords. Read more `,
    link: "https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication",
    custom: false,
  },
  {
    name: "Yahoo",
    icon: LogoYahoo,
    info: `Setting up Yahoo requires you to enable two factor authentication
		  and app specific passwords. Read more `,
    link: "https://help.yahoo.com/kb/SLN15241.html",
    custom: false,
  },
  {
    name: "Yandex",
    icon: LogoYandex,
    info: `Setting up Yandex requires you to enable two factor authentication
		  and app specific passwords. Read more `,
    link: "https://yandex.com/support/id/authorization/app-passwords.html",
    custom: false,
  },
  {
    name: "Frappe Mail",
    icon: LogoFrappeMail,
    info: `Setting up Frappe Mail requires you to have an API key and API Secret of your email account. Read more `,
    link: "https://github.com/frappe/mail",
    custom: true,
  },
  {
    name: "Custom",
    icon: "",
    info: `Use your own IMAP/SMTP settings. Open in Desk`,
    link: "/desk/email-account/new-email-account",
    custom: true,
  },
];

export const emailIcon = {
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
    return "Account name is required";
  }
  if (!state.email_id) {
    return "Email ID is required";
  }
  const validEmail = validateEmailWithZod(state.email_id);
  if (!validEmail) {
    return "Invalid email ID";
  }
  if (service === "Frappe Mail") {
    if (!state.api_key) {
      return "API Key is required";
    }
    if (!state.api_secret) {
      return "API Secret is required";
    }
    return "";
  }
  if (service === "Custom") {
    const hasDomain = Boolean(state.domain);
    const hasManualServers =
      state.email_server && state.incoming_port && state.smtp_server && state.smtp_port;
    if (!hasDomain && !hasManualServers) {
      return "Email Domain or manual server settings are required";
    }
    if (!state.password && !allowMissingPassword) {
      return "Password is required";
    }
    return "";
  }
  if (!state.password && !allowMissingPassword) {
    return "Password is required";
  }
  return "";
}
