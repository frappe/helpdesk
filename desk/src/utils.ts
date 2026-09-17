import { useAuthStore } from "@/stores/auth";
import type { DropdownOption } from "@/types";
import { useClipboard } from "@vueuse/core";
import {
  FeatherIcon,
  call,
  dayjsLocal,
  toast,
  useFileUpload,
} from "frappe-ui";
import { h, ref } from "vue";
import zod from "zod";
import LucideBrushCleaning from "~icons/lucide/brush-cleaning";
import { Icon } from "frappe-ui/icons";
import { getMeta } from "./stores/meta";
import { __ } from "./translation";

export {
  prettyDate,
  shortDuration,
  timeAgo,
  validateEmail,
} from "@helpdesk/shared/utils";

/**
 * Wrapper to create toasts, supplied with default options.
 * https://frappeui.com/components/toast.html
 * @param options - `Toast` options
 */

/**
 * Copy a string to clipboard, and create a toast
 * @param s - String to copy
 */
export async function copy(s: string) {
  const { copy: c } = useClipboard();
  c(s).then(() => toast.success(__("Copied to clipboard.")));
}

/**
 * Get assigned user from `_assign` string. The return value is a `string`,
 * not a `User` object.
 * @param s - `_assign` string (JSON)
 * @returns user id
 */
export function getAssign(s: string): string | undefined {
  const assignJson = JSON.parse(s);
  const arr = Array.isArray(assignJson) ? assignJson : [];
  return arr.slice(-1).pop();
}

export function extractEmail(input: string) {
  const match = input.match(/<([^>]+)>$/); // grabs the part inside <>
  return match ? match[1] : input;
}

export function validateEmailWithZod(email: string) {
  const extractedEmail = extractEmail(email);
  const success = zod.string().email().safeParse(extractedEmail).success;
  return success;
}

/** Dayjs date format derived from the site's System Settings (boot data). */
export function getDateFormat(): string {
  return ((window as any).date_format || "dd-mm-yyyy").toUpperCase();
}

/** Time format from the site's System Settings (boot data). */
export function getTimeFormat(): string {
  return (window as any).time_format || "HH:mm:ss";
}

export function dateFormat(date, format?: string) {
  const _format = format || `${getDateFormat()} ${getTimeFormat()}`;
  if (!date) return "";
  const tzDate = dayjsLocal(date);
  return tzDate.format(_format);
}

export const dateTooltipFormat = "ddd, MMM D, YYYY h:mm A";

export function errorMessage(title, message) {
  toast.error(message);
}

export function formatTime(
  seconds: number,
  config: {
    day?: boolean;
    hour?: boolean;
    minute?: boolean;
    second?: boolean;
    maxUnits?: number;
  } = {
    day: true,
    hour: true,
    minute: true,
    second: true,
  }
) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  const parts: string[] = [];

  if (config.day && days > 0) {
    parts.push(`${days}d`);
  }

  if (config.hour && (hours > 0 || days > 0)) {
    parts.push(`${hours}h`);
  }

  if (config.minute && (minutes > 0 || hours > 0 || days > 0)) {
    parts.push(`${minutes}m`);
  }

  if (config.second) {
    parts.push(
      `${
        remainingSeconds >= 10
          ? remainingSeconds
          : remainingSeconds > 1
          ? "0" + remainingSeconds
          : "0"
      }s`
    );
  }

  const limited = config.maxUnits ? parts.slice(0, config.maxUnits) : parts;
  return limited.join(" ").trim();
}

export function getTimeInSeconds(time: string) {
  // time in the format 1h 2m 3s
  let timeParts = time.split(" ");
  let seconds = 0;
  timeParts.forEach((part) => {
    if (part.endsWith("d")) {
      seconds += parseInt(part) * 24 * 60 * 60; // days
    } else if (part.endsWith("h")) {
      seconds += parseInt(part) * 60 * 60; // hours
    } else if (part.endsWith("m")) {
      seconds += parseInt(part) * 60; // minutes
    } else if (part.endsWith("s")) {
      seconds += parseInt(part); // seconds
    }
  });
  return seconds;
}

export const isCustomerPortal = ref(false);

// The studio-built customer portal, served outside the desk SPA. Customer
// ticket pages live there; the desk only hard-navigates to it.
export const CUSTOMER_PORTAL_ROOT = "/kb";

export function customerPortalTicketUrl(ticketId: string) {
  return `${CUSTOMER_PORTAL_ROOT}/tickets/${ticketId}`;
}

export async function copyToClipboard(
  msg: string = "",
  toastMessage: string = __("Copied to clipboard.")
) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(msg);
  } else {
    let input = document.createElement("input");
    let body = document.querySelector("body");
    body.appendChild(input);
    input.value = msg;
    input.select();
    document.execCommand("copy");
    input.remove();
  }

  toast.success(toastMessage);
}

export const ClearFormattingUtility = {
  label: "Clear formatting",
  icon: LucideBrushCleaning,
  action: (editor) => {
    editor.chain().focus().unsetAllMarks().clearNodes().cleanStyles().run();
  },
  isActive: () => false,
};

export const textEditorMenuButtons = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
  "Separator",
  "Bold",
  "Italic",
  "FontColor",
  "Separator",
  ["Align Left", "Align Center", "Align Right"],
  "Bullet List",
  "Numbered List",
  "Separator",
  "Image",
  "Video",
  "Link",
  "Blockquote",
  "Code",
  "Horizontal Rule",
  [
    "InsertTable",
    "AddColumnBefore",
    "AddColumnAfter",
    "DeleteColumn",
    "AddRowBefore",
    "AddRowAfter",
    "DeleteRow",
    "MergeCells",
    "SplitCell",
    "ToggleHeaderColumn",
    "ToggleHeaderRow",
    "ToggleHeaderCell",
    "DeleteTable",
  ],
  "Separator",
  ClearFormattingUtility,
];

export function isContentEmpty(content: string) {
  if (!content || content === null || content === undefined) {
    return true;
  }
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  if (doc.body.textContent === null) {
    return true;
  }
  return doc.body.textContent.trim() === "";
}

export function normalize(value: any) {
  if (value === null || value === undefined) {
    return "";
  }
  return value;
}

export function isTouchScreenDevice() {
  return "ontouchstart" in document.documentElement;
}

// Lucide names are plain ASCII, so any emoji-presentation or pictographic
// character (or a variation selector, for keycaps like 1️⃣) means a legacy emoji.
export function isEmoji(str: string): boolean {
  return /\p{Emoji_Presentation}|\p{Extended_Pictographic}|\uFE0F/u.test(str);
}

/**
 * Resolves a stored icon value into a renderable component.
 * Supports Lucide icon names from the frappe-ui IconPicker, emojis stored by
 * older views, and pre-resolved icon components, falling back to the ticket icon.
 */
export function getIcon(icon) {
  if (!icon) {
    return h(Icon, { name: "ticket" });
  }
  if (isEmoji(icon)) {
    return h(
      "div",
      { class: "flex items-center justify-center leading-none" },
      icon
    );
  }
  if (typeof icon === "string") {
    return h(Icon, { name: icon });
  }
  return icon;
}
export function formatTimeShort(date: string) {
  const now = dayjsLocal();
  const inputDate = dayjsLocal(date);
  const diffSeconds = now.diff(inputDate, "second");
  const diffMinutes = now.diff(inputDate, "minute");
  const diffHours = now.diff(inputDate, "hour");
  const diffDays = now.diff(inputDate, "day");
  const diffWeeks = now.diff(inputDate, "week");
  const diffMonths = now.diff(inputDate, "month");
  const diffYears = now.diff(inputDate, "year");

  if (diffSeconds < 60) return `${diffSeconds} s`;
  if (diffMinutes < 60) return `${diffMinutes} m`;
  if (diffHours < 24) return `${diffHours} h`;
  if (diffDays < 7) return `${diffDays} d`;
  if (diffWeeks < 4) return `${diffWeeks} w`;
  if (diffMonths < 12) return `${diffMonths} M`;
  return `${diffYears}Y`;
}

function hasArabicContent(content: string) {
  const arabicRegex = /[\u0600-\u06FF]/;
  return arabicRegex.test(content);
}

export function getFontFamily(content: string) {
  const langMap = {
    default: "!font-[Inter]",
    arabic: "!font-[system-ui]",
  };
  let lang = "";
  if (hasArabicContent(content)) {
    lang = "arabic";
  }
  return langMap[lang] || "";
}

/**
 * Parses HTML string and returns the text content with preserved line breaks
 * @param html - HTML string to parse
 * @returns Plain text content with preserved line breaks
 */
export function htmlToText(html: string): string {
  if (!html) return "";

  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");

  const lineBreaks = doc.querySelectorAll("br, p, div, li");
  lineBreaks.forEach((el) => {
    el.after("\n");
  });

  let text = doc.body.textContent || "";

  text = text.replace(/\s+/g, " ");

  text = text.replace(/\n\s*\n/g, "\n");

  return text.trim();
}

/**
 * Format a date according to the user's system settings
 * @param {Date|string} date - Date object or ISO date string
 * @returns {string} Formatted date string in the user's locale and preferences
 */
export function getFormattedDate(date) {
  if (!date) return "";
  const dateObj = dayjsLocal(date);
  if (!dateObj.isValid()) return "";

  return dateObj.format(getDateFormat());
}

export function TemplateOption({ active, option, variant, icon, onClick }) {
  return h(
    "button",
    {
      class: [
        active ? "bg-surface-gray-2" : "text-ink-gray-8",
        "group flex w-full gap-2 items-center rounded-md px-2 py-2 text-base hover:bg-surface-gray-3",
        variant == "danger" ? "text-ink-red-6 hover:bg-ink-red-1" : "",
      ],
      onClick: onClick,
    },
    [renderOptionIcon(icon), h("span", { class: "whitespace-nowrap" }, option)]
  );
}

/**
 * Renders an option icon: `lucide-*` strings as CSS-mask spans (frappe-ui v1),
 * other strings as legacy FeatherIcon, and components as-is.
 */
export function renderOptionIcon(
  icon: string | object | null,
  classes: string[] = ["h-4 w-4 shrink-0"]
) {
  if (!icon) return null;
  if (typeof icon === "string" && icon.startsWith("lucide-")) {
    return h("span", { class: [icon, ...classes], "aria-hidden": true });
  }
  if (typeof icon === "string") {
    return h(FeatherIcon, { name: icon, class: classes, "aria-hidden": true });
  }
  return h(icon, { class: classes, "aria-hidden": true });
}

export function getGridTemplateColumnsForTable(columns) {
  let columnsWidth = columns
    .map((col) => {
      let width = col.width || 1;
      if (typeof width === "number") {
        return width + "fr";
      }
      return width;
    })
    .join(" ");
  return columnsWidth + " 22px";
}

export function uploadFunction(
  file: File,
  doctype: string | null = null,
  docname: string | null = null,
  isPrivate: boolean = true
) {
  let fileUpload = useFileUpload();
  return fileUpload.upload(file, {
    private: isPrivate,
    doctype: doctype,
    docname: docname,
  });
}

export const convertToConditions = ({
  conditions,
  fieldPrefix,
}: {
  conditions: any[];
  fieldPrefix?: string;
}): string => {
  if (!conditions || conditions.length === 0) {
    return "";
  }

  const processCondition = (condition: any): string => {
    if (typeof condition === "string") {
      return condition.toLowerCase();
    }

    if (Array.isArray(condition)) {
      // Nested condition group
      if (Array.isArray(condition[0])) {
        const nestedStr = convertToConditions({
          conditions: condition,
          fieldPrefix,
        });
        return `(${nestedStr})`;
      }

      // Simple condition: [fieldname, operator, value]
      const [field, operator, value] = condition;
      const fieldAccess = fieldPrefix ? `${fieldPrefix}.${field}` : field;

      const operatorMap: Record<string, string> = {
        equals: "==",
        "=": "==",
        "==": "==",
        "!=": "!=",
        "not equals": "!=",
        "<": "<",
        "<=": "<=",
        ">": ">",
        ">=": ">=",
        in: "in",
        "not in": "not in",
        like: "like",
        "not like": "not like",
        is: "is",
        "is not": "is not",
        between: "between",
      };

      let op = operatorMap[operator.toLowerCase()] || operator;

      if (
        (op === "==" || op === "!=") &&
        (String(value).toLowerCase() === "yes" ||
          String(value).toLowerCase() === "no")
      ) {
        let checkVal = String(value).toLowerCase() === "yes";
        if (op === "!=") {
          checkVal = !checkVal;
        }
        return checkVal ? fieldAccess : `not ${fieldAccess}`;
      }

      if (op === "is" && String(value).toLowerCase() === "set") {
        return fieldAccess;
      }
      if (
        (op === "is" && String(value).toLowerCase() === "not set") ||
        (op === "is not" && String(value).toLowerCase() === "set")
      ) {
        return `not ${fieldAccess}`;
      }

      if (op === "like") {
        return `(${fieldAccess} and "${value}" in ${fieldAccess})`;
      }
      if (op === "not like") {
        return `(${fieldAccess} and "${value}" not in ${fieldAccess})`;
      }

      if (
        op === "between" &&
        typeof value === "string" &&
        value.includes(",")
      ) {
        const [start, end] = value.split(",").map((v: string) => v.trim());
        return `(${fieldAccess} >= "${start}" and ${fieldAccess} <= "${end}")`;
      }

      let valueStr = "";
      if (op === "in" || op === "not in") {
        let items: string[];
        if (Array.isArray(value)) {
          items = value.map((v) => `"${String(v).trim()}"`);
        } else if (typeof value === "string") {
          items = value.split(",").map((v) => `"${v.trim()}"`);
        } else {
          items = [`"${String(value).trim()}"`];
        }
        valueStr = `[${items.join(", ")}]`;
        return `(${fieldAccess} and ${fieldAccess} ${op} ${valueStr})`;
      }

      if (typeof value === "string") {
        valueStr = `"${value.replace(/"/g, '\\"')}"`;
      } else if (typeof value === "number" || typeof value === "boolean") {
        valueStr = String(value);
      } else if (value === null || value === undefined) {
        return op === "==" || op === "is" ? `not ${fieldAccess}` : fieldAccess;
      } else {
        valueStr = `"${String(value).replace(/"/g, '\\"')}"`;
      }

      return `${fieldAccess} ${op} ${valueStr}`;
    }

    return "";
  };

  const parts = conditions.map(processCondition);
  return parts.join(" ");
};

export function validateConditions(conditions: any[]): boolean {
  if (!Array.isArray(conditions)) return false;

  // Handle simple condition [field, operator, value]
  if (
    conditions.length === 3 &&
    typeof conditions[0] === "string" &&
    typeof conditions[1] === "string"
  ) {
    return conditions[0] !== "" && conditions[1] !== "" && conditions[2] !== "";
  }

  // Iterate through conditions and logical operators
  for (let i = 0; i < conditions.length; i++) {
    const item = conditions[i];

    // Skip logical operators (they will be validated by their position)
    if (item === "and" || item === "or") {
      // Ensure logical operators are not at start/end and not consecutive
      if (
        i === 0 ||
        i === conditions.length - 1 ||
        conditions[i - 1] === "and" ||
        conditions[i - 1] === "or"
      ) {
        return false;
      }
      continue;
    }

    // Handle nested conditions (arrays)
    if (Array.isArray(item)) {
      if (!validateConditions(item)) {
        return false;
      }
    } else if (item !== undefined && item !== null) {
      return false;
    }
  }

  return conditions.length > 0;
}

export async function removeAttachmentFromServer(attachment: string) {
  await call("frappe.client.delete", {
    doctype: "File",
    name: attachment,
  });
}

function getParentChildField(name: string) {
  let [_, parent, child] = name.split("-");
  return [parent, child];
}

export function getFieldDependencyLabel(name: string) {
  const { getField } = getMeta("HD Ticket");
  let [parent, child] = getParentChildField(name);
  parent = getField(parent)?.label || parent;
  child = getField(child)?.label || child;
  return `${parent} → ${child}`;
}

/**
 * @param {Object} config - Configuration object
 * @param {Ref<boolean>} config.isConfirmingDelete - Ref to track confirmation state
 * @param {Function} config.onConfirmDelete - Callback when delete is confirmed
 * @returns {Array} Array of option objects for use in dropdowns
 */
export function ConfirmDelete({ isConfirmingDelete, onConfirmDelete }) {
  return [
    {
      label: "Delete",
      component: (props) =>
        TemplateOption({
          option: "Delete",
          icon: "lucide-trash-2",
          active: props.active,
          variant: "grey",
          onClick: (event) => {
            event.preventDefault();
            event.stopImmediatePropagation();
            isConfirmingDelete.value = true;
          },
        }),
      condition: () => !isConfirmingDelete.value,
    },
    {
      label: "Confirm Delete",
      component: (props) =>
        TemplateOption({
          option: "Confirm Delete",
          icon: "lucide-trash-2",
          active: props.active,
          variant: "danger",
          onClick: () => {
            onConfirmDelete();
            // Reset state after confirming
            isConfirmingDelete.value = false;
          },
        }),
      condition: () => isConfirmingDelete.value,
    },
  ];
}

export function getRandom(len = 4) {
  let text = "";
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

  Array.from({ length: len }).forEach(() => {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  });

  return text;
}

export function isElementInViewport(el: HTMLElement) {
  if (!el) return false;
  const rect = el.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= window.innerHeight &&
    rect.right <= window.innerWidth
  );
}

export function parseApiOptions(
  options: string[] | DropdownOption[]
): DropdownOption[] | [] {
  if (!options?.length) return [];
  return (
    options
      .filter((o) => Boolean(o))
      .map((o) => {
        if (
          typeof o === "object" &&
          o.hasOwnProperty("label") &&
          o.hasOwnProperty("value")
        ) {
          return o;
        } else {
          return {
            label: o?.toString(),
            value: o as string,
          };
        }
      }) || []
  );
}

export function openContact(name: string) {
  const url = window.location.origin + "/helpdesk/contacts/" + name;
  window.open(url, "_blank");
}

const COLOR_PROPS = new Set([
  "color",
  "background",
  "background-color",
  "border-color",
]);

// Strip color-related inline styles + bgcolor/color attrs so iframe CSS controls colors.
export function stripEmailColors(html: string): string {
  if (!html) return html;
  const div = document.createElement("div");
  div.innerHTML = html;

  div.querySelectorAll("[style]").forEach((el) => {
    const styles = el.getAttribute("style") || "";
    const filtered = styles
      .split(";")
      .map((s) => s.trim())
      .filter((s) => {
        if (!s) return false;
        const prop = s.split(":")[0].trim().toLowerCase();
        return !COLOR_PROPS.has(prop);
      })
      .join("; ");
    if (filtered) el.setAttribute("style", filtered);
    else el.removeAttribute("style");
  });

  div
    .querySelectorAll("[bgcolor]")
    .forEach((el) => el.removeAttribute("bgcolor"));
  div
    .querySelectorAll("font[color]")
    .forEach((el) => el.removeAttribute("color"));

  return div.innerHTML;
}

// Shared reactive mirror of <html data-theme> for JS-driven theme-aware components
export const dataTheme = ref<string>(
  (typeof document !== "undefined" &&
    document.documentElement.getAttribute("data-theme")) ||
    "light"
);

if (typeof window !== "undefined") {
  new MutationObserver(() => {
    const next = document.documentElement.getAttribute("data-theme") || "light";
    if (next !== dataTheme.value) dataTheme.value = next;
  }).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
}

export function buildPercentageChange(
  value: number | null,
  negativeIsBetter: boolean = true
) {
  // No change (or no comparison): stay neutral — never green/red, no up/down arrow.
  if (value === null || value === undefined || value === 0) {
    return { icon: "", value: "0", color: "text-ink-gray-5" };
  }
  const isPositive = value > 0;
  const isGood = negativeIsBetter ? !isPositive : isPositive;
  // Cap the magnitude at 100% so large swings (e.g. +3186%) stay readable.
  const capped = Math.min(Math.abs(value), 100);
  return {
    icon: isPositive ? "lucide-arrow-up-right" : "lucide-arrow-down-left",
    value: isPositive ? `+${capped}` : `-${capped}`,
    color: isGood ? "text-ink-green-6" : "text-ink-red-6",
  };
}

export function hasPermission() {
  const authStore = useAuthStore();
  return authStore.isAdmin || authStore.isManager;
}

export function getErrorMessage(
  error: any,
  showToast: boolean = false
): string {
  const msg = error.exc_type
    ? (error.messages || error.message || []).join(", ")
    : error.message;
  if (showToast) {
    toast.error(msg);
  }
  return msg;
}
const emailsToStr = (emails: readonly string[]) => emails.join(", ");

export function handleInviteUserSuccess(
  data: Record<
    | "disabled_user_emails"
    | "accepted_invite_emails"
    | "pending_invite_emails"
    | "invited_emails",
    string[]
  >
) {
  let emailsStr = emailsToStr(data.invited_emails);
  if (emailsStr.trim() !== "") {
    toast.success(`${emailsStr} invited successfully`);
  }
  emailsStr = emailsToStr(data.disabled_user_emails);
  if (emailsStr.trim() !== "") {
    toast.info(`${emailsStr} already present and disabled`);
  }
  emailsStr = emailsToStr(data.pending_invite_emails);
  if (emailsStr.trim() !== "") {
    toast.info(`${emailsStr} already invited`);
  }
  emailsStr = emailsToStr(data.accepted_invite_emails);
  if (emailsStr.trim() !== "") {
    toast.info(`${emailsStr} already present`);
  }
}
