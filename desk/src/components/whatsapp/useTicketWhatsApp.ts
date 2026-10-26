import { serverInstant } from "@helpdesk/shared/utils";
import { useNow } from "@vueuse/core";
import { useMessages } from "@whatsapp/ui";
import { createResource } from "frappe-ui";
import { computed, reactive, toValue, watch, type MaybeRefOrGetter } from "vue";
import { isWhatsAppInstalled } from "./conversationTab";

/** What helpdesk.integrations.whatsapp.api.get_conversation returns. */
export interface Conversation {
  installed: boolean;
  to: string | null;
  reply_window_open: boolean;
  reply_window_closes_at: string | null;
  business_number: string | null;
  /** WA Template names the customer's Business Number may send */
  templates: string[];
}

interface TicketLike {
  name?: string;
  source?: string;
  contact?: string;
}

/**
 * One ticket's WhatsApp conversation: the @whatsapp/ui messages controller plus
 * Helpdesk's own view of who to send to and whether the reply window is open.
 * Call it once per page and hand it to the thread and the composer.
 */
export function useTicketWhatsApp(
  ticket: MaybeRefOrGetter<TicketLike | undefined>
) {
  const ticketName = () => String(toValue(ticket)?.name ?? "");
  const enabled = () =>
    isWhatsAppInstalled() && toValue(ticket)?.source === "WhatsApp";
  const conversation = conversationResource(ticketName, enabled);

  const messages = useMessages({
    references: () => [["HD Ticket", ticketName()]],
    to: () => conversation.data?.to ?? undefined,
    enabled,
  });

  const now = useNow({ interval: 60_000 });
  const windowOpen = computed(() => isWindowOpen(conversation.data, now.value));

  // a new message can reopen the window or change who to answer
  watch(
    () => messages.messages.length,
    () => enabled() && conversation.reload()
  );
  // the phone page outlives a ticket switch, so a draft must not follow the agent
  watch(ticketName, () => messages.reset());

  return reactive({
    messages,
    conversation: computed(() => conversation.data as Conversation | undefined),
    windowOpen,
    enabled: computed(enabled),
    ticketName: computed(ticketName),
    contactName: computed(() => toValue(ticket)?.contact || ""),
  });
}

export type TicketWhatsApp = ReturnType<typeof useTicketWhatsApp>;

function conversationResource(
  ticketName: () => string,
  enabled: () => boolean
) {
  const resource = createResource({
    url: "helpdesk.integrations.whatsapp.api.get_conversation",
    makeParams: () => ({ ticket: ticketName() }),
  });
  watch([ticketName, enabled], () => enabled() && resource.reload(), {
    immediate: true,
  });
  return resource;
}

function isWindowOpen(data: Conversation | undefined, now: Date): boolean {
  if (!data?.reply_window_open) return false;
  if (!data.reply_window_closes_at) return true;
  return serverInstant(data.reply_window_closes_at).isAfter(now);
}
