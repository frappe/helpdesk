export type EmailEventName = "share-feedback" | "acknowledgement";

export type EmailEvent = {
    name: EmailEventName;
    label: string;
    description: string;
};

export type AtLeastOneEmailEvent = [EmailEvent, ...EmailEvent[]];
