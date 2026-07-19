import { useAuthStore } from "@/stores/auth";
import type { DropdownOption } from "@/types";
import { useClipboard } from "@vueuse/core";
import {
  FeatherIcon,
  call,
  dayjs,
  dayjsLocal,
  toast,
  useFileUpload,
} from "frappe-ui";
import { gemoji } from "gemoji";
import { h, markRaw, ref } from "vue";
import zod from "zod";
import LucideBrushCleaning from "~icons/lucide/brush-cleaning";
import TicketIcon from "./components/icons/TicketIcon.vue";
import { getMeta } from "./stores/meta";
import { __ } from "./translation";

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

export function validateEmail(email) {
  const regExp =
    /^((?:"[\p{L}\p{M}\d .,_%+-]+"|[\p{L}\d._%+-]+)\s)?<([\p{L}\d._%+-]+@[\p{L}\d.-]+\.[\p{L}]{2,})>$|^([\p{L}\d._%+-]+@[\p{L}\d.-]+\.[\p{L}]{2,})$/u;
  return regExp.test(email);
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

export function timeAgo(date) {
  return prettyDate(date);
}

export function getBrowserTimezone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function prettyDate(date, mini = false) {
  if (!date) return "";

  if (typeof date == "string") {
    date = dayjsLocal(date);
  }

  let nowDatetime = dayjsLocal();
  let diff = nowDatetime.diff(date, "seconds");
  let absDiff = Math.abs(diff);

  // Day-level labels ("Yesterday", "N days ago"...) count calendar dates, not
  // elapsed 24h windows — otherwise they track time-of-day and an event lands
  // in the wrong day around midnight. Sub-day labels below still use elapsed
  // seconds, so recent events keep precise "minutes/hours ago".
  let dayDiff = nowDatetime.startOf("day").diff(date.startOf("day"), "day");

  if (isNaN(dayDiff)) return "";

  if (mini) {
    // Return short format of time difference
    if (absDiff < 86400) {
      // Within a day — show sub-day granularity (past or future).
      if (absDiff < 60) return __("Now");
      if (absDiff < 3600) {
        const minutes = Math.floor(absDiff / 60);
        return diff >= 0 ? __("{0} m", [minutes]) : __("in {0} m", [minutes]);
      }
      const hours = Math.floor(absDiff / 3600);
      return diff >= 0 ? __("{0} h", [hours]) : __("in {0} h", [hours]);
    } else if (diff < 0) {
      const ahead = -dayDiff;
      if (ahead === 1) {
        return __("Tomorrow");
      } else if (ahead < 7) {
        return __("in {0} d", [ahead]);
      } else if (ahead < 31) {
        return __("in {0} w", [Math.floor(ahead / 7)]);
      } else if (ahead < 365) {
        return __("in {0} M", [Math.floor(ahead / 30)]);
      } else {
        return __("in {0} y", [Math.floor(ahead / 365)]);
      }
    } else {
      if (dayDiff < 7) {
        return __("{0} d", [dayDiff]);
      } else if (dayDiff < 31) {
        return __("{0} w", [Math.floor(dayDiff / 7)]);
      } else if (dayDiff < 365) {
        return __("{0} M", [Math.floor(dayDiff / 30)]);
      } else {
        return __("{0} y", [Math.floor(dayDiff / 365)]);
      }
    }
  } else {
    // Return long format of time difference
    if (absDiff < 86400) {
      // Within a day — show sub-day granularity (past or future).
      if (absDiff < 60) return __("Just now");
      if (diff >= 0) {
        if (absDiff < 120) return __("1 minute ago");
        if (absDiff < 3600) return __("{0} minutes ago", [Math.floor(absDiff / 60)]);
        if (absDiff < 7200) return __("1 hour ago");
        return __("{0} hours ago", [Math.floor(absDiff / 3600)]);
      }
      if (absDiff < 120) return __("In 1 minute");
      if (absDiff < 3600) return __("In {0} minutes", [Math.floor(absDiff / 60)]);
      if (absDiff < 7200) return __("In 1 hour");
      return __("In {0} hours", [Math.floor(absDiff / 3600)]);
    } else if (diff < 0) {
      const ahead = -dayDiff;
      if (ahead === 1) {
        return __("Tomorrow");
      } else if (ahead < 7) {
        return __("In {0} days", [ahead]);
      } else if (ahead < 31) {
        return __("In {0} weeks", [Math.floor(ahead / 7)]);
      } else if (ahead < 365) {
        return __("In {0} months", [Math.floor(ahead / 30)]);
      } else if (ahead < 730) {
        return __("In 1 year");
      } else {
        return __("In {0} years", [Math.floor(ahead / 365)]);
      }
    } else {
      if (dayDiff === 1) {
        return __("Yesterday");
      } else if (dayDiff < 7) {
        return __("{0} days ago", [dayDiff]);
      } else if (dayDiff < 14) {
        return __("1 week ago");
      } else if (dayDiff < 31) {
        return __("{0} weeks ago", [Math.floor(dayDiff / 7)]);
      } else if (dayDiff < 62) {
        return __("1 month ago");
      } else if (dayDiff < 365) {
        return __("{0} months ago", [Math.floor(dayDiff / 30)]);
      } else if (dayDiff < 730) {
        return __("1 year ago");
      } else {
        return __("{0} years ago", [Math.floor(dayDiff / 365)]);
      }
    }
  }
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

export function isEmoji(str) {
  const emojiList = gemoji.map((emoji) => emoji.emoji);
  return emojiList.includes(str);
}

export function getIcon(icon) {
  if (isEmoji(icon)) {
    return h("div", icon);
  }
  return icon || markRaw(TicketIcon);
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
        variant == "danger" ? "text-ink-red-3 hover:bg-ink-red-1" : "",
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
  doctype: string = null,
  docname: string = null
) {
  let fileUpload = useFileUpload();
  return fileUpload.upload(file, {
    private: true,
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
  if (!options.length) return [];
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

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;
const YEAR = 365 * DAY;

/**
 * Compact relative duration between `target` and now, ignoring direction.
 * Examples: `1y`, `4 days 4h`, `2h 20m`, `5m`.
 */
export function shortDuration(target: string | Date): string {
  const seconds = Math.abs(dayjs(target).diff(dayjs(), "second"));
  if (seconds >= YEAR) {
    const years = Math.floor(seconds / YEAR);
    return `${years} ${years === 1 ? "year" : "years"}`;
  }
  if (seconds >= MONTH) {
    const months = Math.floor(seconds / MONTH);
    return `${months} ${months === 1 ? "month" : "months"}`;
  }
  if (seconds >= DAY) {
    const days = Math.floor(seconds / DAY);
    const hours = Math.floor((seconds % DAY) / HOUR);
    const dayLabel = `${days} ${days === 1 ? "day" : "days"}`;
    return hours ? `${dayLabel} ${hours}h` : dayLabel;
  }
  if (seconds >= HOUR) {
    const hours = Math.floor(seconds / HOUR);
    const minutes = Math.floor((seconds % HOUR) / MINUTE);
    return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  return `${Math.floor(seconds / MINUTE)}m`;
}

export function buildPercentageChange(
  value: number | null,
  negativeIsBetter: boolean = true
) {
  // No change (or no comparison): stay neutral — never green/red, no up/down arrow.
  if (value === null || value === undefined || value === 0) {
    return { icon: "lucide-arrow-right", value: "0", color: "text-ink-gray-5" };
  }
  const isPositive = value > 0;
  const isGood = negativeIsBetter ? !isPositive : isPositive;
  // Cap the magnitude at 100% so large swings (e.g. +3186%) stay readable.
  const capped = Math.min(Math.abs(value), 100);
  return {
    icon: isPositive ? "lucide-arrow-up-right" : "lucide-arrow-down-left",
    value: isPositive ? `+${capped}` : `-${capped}`,
    color: isGood ? "text-ink-green-3" : "text-ink-red-3",
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
