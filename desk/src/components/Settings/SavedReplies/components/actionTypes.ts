import { __ } from "@/translation";
import { DropdownOption, SavedReplyActionType } from "@/types";
import { isContentEmpty } from "@/utils";
import type { Component } from "vue";
import LucideCircleDot from "~icons/lucide/circle-dot";
import LucideMessageSquare from "~icons/lucide/message-square";
import LucideSignal from "~icons/lucide/signal";
import LucideTag from "~icons/lucide/tag";
import LucideTicket from "~icons/lucide/ticket";
import LucideUserCheck from "~icons/lucide/user-check";
import LucideUserPlus from "~icons/lucide/user-plus";
import LucideUsers from "~icons/lucide/users";

export type ActionControl =
  | "select"
  | "combobox"
  | "multiselect"
  | "editor"
  | "none";

/** A value option; tags carry a colour and agents an avatar. */
export type ActionOption = DropdownOption & {
  color?: string | undefined;
  image?: string | undefined;
};

export interface ActionTypeConfig {
  label: string;
  chipLabel: string;
  /** Noun used in validation messages, e.g. "Ticket Type can't be empty" */
  fieldname?: string;
  icon: Component;
  control: ActionControl;
  /** Muted clarifier shown in the row's value area for no-value actions */
  hint?: string;
}

/** Display config per action type, in menu/display order. */
export const ACTION_TYPES: Record<SavedReplyActionType, ActionTypeConfig> = {
  "Set Status": {
    label: __("Set status"),
    chipLabel: __("Status"),
    fieldname: __("Status"),
    icon: LucideCircleDot,
    control: "select",
  },
  "Set Priority": {
    label: __("Set priority"),
    chipLabel: __("Priority"),
    fieldname: __("Priority"),
    icon: LucideSignal,
    control: "select",
  },
  "Set Team": {
    label: __("Set team"),
    chipLabel: __("Team"),
    fieldname: __("Team"),
    icon: LucideUsers,
    control: "combobox",
  },
  "Set Ticket Type": {
    label: __("Set ticket type"),
    chipLabel: __("Type"),
    fieldname: __("Ticket Type"),
    icon: LucideTicket,
    control: "combobox",
  },
  "Assign Agent": {
    label: __("Assign agent"),
    chipLabel: __("Assign"),
    fieldname: __("Agent"),
    icon: LucideUserPlus,
    control: "combobox",
  },
  "Assign to Me": {
    label: __("Assign to me"),
    chipLabel: __("Assign to me"),
    icon: LucideUserCheck,
    control: "none",
    hint: __("The agent who sends the reply"),
  },
  "Add Tag": {
    label: __("Add tags"),
    chipLabel: __("Tag"),
    icon: LucideTag,
    control: "multiselect",
  },
  "Remove Tag": {
    label: __("Remove tags"),
    chipLabel: __("Remove tag"),
    icon: LucideTag,
    control: "multiselect",
  },
  "Add Comment": {
    label: __("Add comment"),
    chipLabel: __("Comment"),
    fieldname: __("Comment"),
    icon: LucideMessageSquare,
    control: "editor",
  },
};

/** Action picker groups; icons alone can't separate the assignment pair. */
export const ACTION_MENU_GROUPS: {
  label: string;
  types: SavedReplyActionType[];
}[] = [
  {
    label: __("Fields"),
    types: ["Set Status", "Set Priority", "Set Team", "Set Ticket Type"],
  },
  { label: __("Assignment"), types: ["Assign Agent", "Assign to Me"] },
  { label: __("Tags"), types: ["Add Tag", "Remove Tag"] },
  { label: __("Comment"), types: ["Add Comment"] },
];

/** Only one of these can be used per reply. */
export const ASSIGNMENT_ACTIONS: SavedReplyActionType[] = [
  "Assign Agent",
  "Assign to Me",
];

export function actionNeedsValue(type: SavedReplyActionType): boolean {
  return ACTION_TYPES[type].control !== "none";
}

/** Empty check that understands rich-text values like `<p></p>`. */
export function isActionValueEmpty(
  type: SavedReplyActionType,
  value: string | undefined
): boolean {
  if (ACTION_TYPES[type].control === "editor") return isContentEmpty(value);
  return !value?.trim();
}

export function isTagAction(type: SavedReplyActionType): boolean {
  return ACTION_TYPES[type].control === "multiselect";
}
