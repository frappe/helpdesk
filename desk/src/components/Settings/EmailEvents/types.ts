export type EmailEventName = "share-feedback";

export type EmailEvent = {
    name: EmailEventName;
    label: string;
    description: string;
};

export type AtLeastOneEmailEvent = [EmailEvent, ...EmailEvent[]];
