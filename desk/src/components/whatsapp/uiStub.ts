/** Stands in for @whatsapp/ui when the whatsapp app is not on the bench; nothing here is ever shown. */
import { defineComponent, reactive } from "vue";

const Empty = defineComponent({ name: "WhatsAppUIStub", render: () => null });
const nothing = async () => null;

export const MessageList = Empty;
export const MessageBubble = Empty;
export const MessageInput = Empty;
export const TemplateContent = Empty;
export const TemplateButtons = Empty;
export const AccountForm = Empty;
export const AppendActionsTable = Empty;
export const TemplateForm = Empty;
export const TemplatePreview = Empty;
export const TemplateBodyEditor = Empty;
export const MediaPreviewDialog = Empty;
export const ReactionPicker = Empty;

export function useMessages() {
  return reactive({
    messages: [],
    loading: false,
    sending: false,
    error: null,
    serviceWindow: null,
    reload: nothing,
    send: nothing,
    react: nothing,
    draft: "",
    pendingType: "document",
    replyTo: null,
    canSend: false,
    setDraft: () => {},
    setReplyTo: () => {},
    clearReply: () => {},
    attach: () => {},
    clearAttachment: () => {},
    buildPayload: () => null,
    reset: () => {},
  });
}

export function useTemplates() {
  return reactive({
    templates: [],
    loading: false,
    error: null,
    reload: nothing,
    sendTemplate: nothing,
    createTemplate: nothing,
  });
}

export function useAccount() {
  return reactive({ doc: {}, isNew: true, isDirty: false, saving: false, save: nothing, reload: nothing });
}

export function useTemplate() {
  return reactive({ doc: {}, isNew: true, isDirty: false, saving: false, save: nothing, reload: nothing });
}

export type MessagesController = ReturnType<typeof useMessages>;
export type TemplatesController = ReturnType<typeof useTemplates>;
export type WhatsAppMessage = { name: string; direction: "Incoming" | "Outgoing" };
export type WhatsAppTemplate = Record<string, any> & { name: string };
export type ReactPayload = { messageName: string; emoji: string };
