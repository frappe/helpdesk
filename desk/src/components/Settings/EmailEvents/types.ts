export type EmailEventName = "share-feedback" | "acknowledgement" | "reply-email-to-agents" | "reply-via-agent";

export type EmailEvent = {
    name: EmailEventName;
    label: string;
    description: string;
};

export type AtLeastOneEmailEvent = [EmailEvent, ...EmailEvent[]];
