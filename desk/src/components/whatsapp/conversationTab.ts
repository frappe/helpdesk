import { EmailIcon } from "@/components/icons";
import { __ } from "@/translation";
import type { TabObject } from "@/types";
import WhatsAppIcon from "./WhatsAppIcon.vue";

/** Adds the conversation tab: first on WhatsApp tickets so they open on it, right after Activity otherwise. */
export function withConversationTab(tabs: TabObject[], isWhatsApp: boolean): TabObject[] {
  // a WhatsApp ticket has no conversation to show without the whatsapp app
  if (isWhatsApp && !isWhatsAppInstalled()) return tabs;
  const tab = conversationTab(isWhatsApp);
  if (isWhatsApp) return [tab, ...tabs];
  const index = tabs.findIndex(({ value }) => value === "activity") + 1;
  return [...tabs.slice(0, index), tab, ...tabs.slice(index)];
}

/** True when the whatsapp app is installed on this site. */
export function isWhatsAppInstalled(): boolean {
  return Boolean(window.apps?.includes("whatsapp"));
}

/** The tab holding a ticket's conversation: WhatsApp for WhatsApp tickets, Emails for the rest. */
function conversationTab(isWhatsApp: boolean): TabObject {
  if (isWhatsApp)
    return { value: "whatsapp", label: __("WhatsApp"), iconLeft: WhatsAppIcon };
  return { value: "email", label: __("Emails"), iconLeft: EmailIcon };
}
