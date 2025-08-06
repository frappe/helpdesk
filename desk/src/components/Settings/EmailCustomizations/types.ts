export type EmailTypeName = "share-feedback";

export type EmailType = {
    name: EmailTypeName;
    label: string;
    description: string;
};

export type AtLeastOneEmailType = [EmailType, ...EmailType[]];
