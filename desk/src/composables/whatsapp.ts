import { createResource } from "frappe-ui";
import { ref } from "vue";

// Whether the frappe_whatsapp transport app is installed on the site. Gates the
// WhatsApp tab out entirely when the app is absent, so vanilla Helpdesk is
// unaffected.
export const isWhatsAppInstalled = ref(false);

// Whether an active outgoing WhatsApp account is configured. The tab only sends
// when this is true; installed-but-unconfigured shows the thread read-only.
export const whatsAppEnabled = ref(false);

createResource({
  url: "helpdesk.integrations.whatsapp.api.is_whatsapp_installed",
  cache: "whatsapp:installed",
  auto: true,
  onSuccess: (data: boolean) => {
    isWhatsAppInstalled.value = Boolean(data);
  },
});

createResource({
  url: "helpdesk.integrations.whatsapp.api.is_whatsapp_enabled",
  cache: "whatsapp:enabled",
  auto: true,
  onSuccess: (data: boolean) => {
    whatsAppEnabled.value = Boolean(data);
  },
});
