import { useClipboard, useDateFormat, useTimeAgo } from "@vueuse/core";
import dayjs from "dayjs";
import { call, toast, useFileUpload } from "frappe-ui";
import { gemoji } from "gemoji";
import { h, markRaw, ref } from "vue";
import zod from "zod";
import TicketIcon from "./components/icons/TicketIcon.vue";
import { getMeta } from "./stores/meta";
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
        return `${fieldAccess} and "${value}" in ${fieldAccess}`;
      }
      if (op === "not like") {
        return `${fieldAccess} and "${value}" not in ${fieldAccess}`;
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
        return `${fieldAccess} and ${fieldAccess} ${op} ${valueStr}`;
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

export async function removeAttachmentFromServer(attachment: string) {
  await call("frappe.client.delete", {
    doctype: "File",
    name: attachment,
  });
}
<<<<<<< HEAD
=======

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
<<<<<<< HEAD
>>>>>>> 43efe7f8 (fix: update field dependency script)
=======

/**
 * Creates a pair of delete/confirm delete options for dropdowns
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
          icon: "trash-2",
          active: props.active,
          variant: "grey",
          onClick: (event) => {
            event.preventDefault();
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
          icon: "trash-2",
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
>>>>>>> 5757901c (fix: common util function for delete/confirmDelete option)
