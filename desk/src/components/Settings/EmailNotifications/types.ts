export type NotificationName = "share_feedback" | "acknowledgement" | "reply_to_agents" | "reply_via_agent";

export type Notification = {
    name: NotificationName;
    label: string;
    description: string;
};

export type AtLeastOneNotifcation = [Notification, ...Notification[]];

export type BaseSettings = {
    enabled: boolean;
    content: string;
};
