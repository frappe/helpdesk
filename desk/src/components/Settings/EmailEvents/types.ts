export type EmailEventName = "share-feedback" | "acknowledgement" | "reply-email-to-agents";

export type EmailEvent = {
    name: EmailEventName;
    label: string;
    description: string;
};

export type AtLeastOneEmailEvent = [EmailEvent, ...EmailEvent[]];
