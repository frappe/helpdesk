import { useClipboard, useDateFormat, useTimeAgo } from "@vueuse/core";
import dayjs from "dayjs";
import { call, FeatherIcon, toast, useFileUpload } from "frappe-ui";
import { gemoji } from "gemoji";
import { h, markRaw, ref } from "vue";
import zod from "zod";
import TicketIcon from "./components/icons/TicketIcon.vue";
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
  c(s).then(() => toast.success("Copied to clipboard"));
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
    /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return regExp.test(email);
}

export function validateEmailWithZod(email: string) {
  const success = zod.string().email().safeParse(email).success;
  return success;
}

export function dateFormat(date, format) {
  const _format = format || "DD-MM-YYYY HH:mm:ss";
  return useDateFormat(date, _format).value;
}

export function timeAgo(date) {
  return useTimeAgo(date).value;
}

export const dateTooltipFormat = "ddd, MMM D, YYYY h:mm A";

export function errorMessage(title, message) {
  toast.error(message);
}

export function formatTime(seconds) {
  const days = Math.floor(seconds / (3600 * 24));
  const hours = Math.floor((seconds % (3600 * 24)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let formattedTime = "";

  if (days > 0) {
    formattedTime += `${days}d `;
  }

  if (hours > 0 || days > 0) {
    formattedTime += `${hours}h `;
  }

  if (minutes > 0 || hours > 0 || days > 0) {
    formattedTime += `${minutes}m `;
  }

  formattedTime += `${
    remainingSeconds >= 10 ? remainingSeconds : "0" + remainingSeconds
  }s`;

  return formattedTime.trim();
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
  toastMessage: string = "Copied to clipboard"
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

export const textEditorMenuButtons = [
  "Paragraph",
  ["Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"],
  "Separator",
  "Bold",
  "Italic",
  "Separator",
  "Bullet List",
  "Numbered List",
  "Separator",
  "Align Left",
  "Align Center",
  "Align Right",
  "FontColor",
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
];

export function isContentEmpty(content: string) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  return doc.body.textContent === "";
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
  const now = dayjs();
  const inputDate = dayjs.tz(date);
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
    default: "!font-[InterVar]",
    arabic: "!font-[system-ui]",
  };
  let lang = "default";
  if (hasArabicContent(content)) {
    lang = "arabic";
  }
  return langMap[lang];
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

export async function removeAttachmentFromServer(attachment: string) {
  await call("frappe.client.delete", {
    doctype: "File",
    name: attachment,
  });
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
export function getFormat(date) {
  if (!date) return "";

  const dateObj = date instanceof Date ? date : new Date(date);
  if (isNaN(dateObj.getTime())) return "";

  // Use the browser's default locale and options
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  }).format(dateObj);
}

export function TemplateOption({ active, option, variant, icon, onClick }) {
  return h(
    "button",
    {
      class: [
        active ? "bg-surface-gray-2" : "text-ink-gray-8",
        "group flex w-full gap-2 items-center rounded-md px-2 py-2 text-base",
        variant == "danger" ? "text-ink-red-3 hover:bg-ink-red-1" : "",
      ],
      onClick: onClick,
    },
    [
      icon
        ? h(FeatherIcon, {
            name: icon,
            class: ["h-4 w-4 shrink-0"],
            "aria-hidden": true,
          })
        : null,
      h("span", { class: "whitespace-nowrap" }, option),
    ]
  );
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

export const convertToConditions = ({
  conditions,
  isNested = false,
  fieldPrefix,
}: {
  conditions: any;
  isNested?: boolean;
  fieldPrefix?: string;
}): string => {
  if (!conditions) {
    return "";
  }

  if (!Array.isArray(conditions)) {
    conditions = [conditions];
  }

  const conditionsStr: string[] = [];

  for (const condition of conditions) {
    const field = condition.field;
    let operator = (condition.operator || "==").toLowerCase();
    const value = condition.value;

    // Handle nested conditions
    if (field === "group" && Array.isArray(value)) {
      const nestedCondition = convertToConditions({
        conditions: value,
        isNested: true,
        fieldPrefix,
      });
      conditionsStr.push(`(${nestedCondition})`);
      continue;
    }

    // Skip if field is not properly defined
    if (typeof field !== "object" || !field.fieldname) {
      continue;
    }

    const fieldname = field.fieldname;
    const fieldtype = field.fieldtype || "";
    const fieldAccess = fieldPrefix ? `${fieldPrefix}.${fieldname}` : fieldname;

    // Operator mapping
    const operatorMap: Record<string, string> = {
      equals: "==",
      "=": "==",
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
      timespan: "timespan",
    };
    let op = operatorMap[operator] || operator;

    let valueStr = "";
    let conditionStr = "";
    if (typeof value === "string") {
      if (fieldtype === "Check") {
        if (["yes", "true", "1"].includes(value.toLowerCase())) {
          valueStr = "1";
        } else {
          valueStr = "0";
        }
        if (op === "==" && valueStr === "1") {
          conditionsStr.push(fieldAccess);
          continue;
        } else if (op === "==" && valueStr === "0") {
          conditionsStr.push(`not ${fieldAccess}`);
          continue;
        }
      } else if (op === "timespan") {
        conditionsStr.push(`# Timespan: ${value} not implemented`);
        continue;
      } else if (op === "between" && value.includes(",")) {
        const [start, end] = value.split(",").map((v: string) => v.trim());
        conditionsStr.push(
          `(${fieldAccess} >= '${start}' and ${fieldAccess} <= '${end}')`
        );
        continue;
      } else if ((op === "in" || op === "not in") && value.includes(",")) {
        const items = value.split(",").map((v: string) => `'${v.trim()}'`);
        valueStr = `[${items.join(", ")}]`;
        conditionStr = `${fieldAccess} ${op} ${valueStr}`;
      } else if (op === "like") {
        conditionStr = `'${value}' in ${fieldAccess}`;
      } else if (op === "not like") {
        conditionStr = `'${value}' not in ${fieldAccess}`;
      } else if (op === "is" && value.toLowerCase() === "set") {
        conditionStr = fieldAccess;
      } else if (op === "is" && value.toLowerCase() === "not set") {
        conditionStr = `not ${fieldAccess}`;
      } else {
        valueStr = `'${value}'`;
        conditionStr = `${fieldAccess} ${op} ${valueStr}`;
      }
    } else if (typeof value === "number" || typeof value === "boolean") {
      valueStr =
        typeof value === "boolean"
          ? String(value).toLowerCase()
          : String(value);
      conditionStr = `${fieldAccess} ${op} ${valueStr}`;
    } else if (value === null || value === undefined) {
      valueStr = "None";
      conditionStr = `${fieldAccess} ${op} ${valueStr}`;
    } else {
      valueStr = String(value);
      conditionStr = `${fieldAccess} ${op} ${valueStr}`;
    }

    if (
      fieldtype === "Check" &&
      op === "==" &&
      (valueStr === "0" || valueStr === "1")
    ) {
      if (valueStr === "1") {
        conditionStr = fieldAccess;
      } else {
        conditionStr = `not ${fieldAccess}`;
      }
    }

    conditionsStr.push(conditionStr);
  }

  if (conditionsStr.length === 0) {
    return "";
  }

  // Use conjunction from the last processed condition (default to 'and')
  const conjunction = (conditions[0]?.conjunction || "and").toLowerCase();
  let result = conditionsStr.join(` ${conjunction} `);

  if (
    !isNested &&
    conditions.length === 1 &&
    !result.includes("(") &&
    !result.includes(")")
  ) {
    return result;
  }

  result = result.replace(/  +/g, " ").replace(/  +/g, " ").trim();

  if (isNested && conditions.length > 1) {
    result = `(${result})`;
  }

  // Remove any double parentheses
  while (result.includes("((") && result.includes("))")) {
    result = result.replace("((", "(").replace("))", ")");
  }

  return result;
};
