import { useClipboard } from "@vueuse/core";
import { call, dayjs, dialog, getConfig, toast } from "frappe-ui";
import type { Ref } from "vue";

import { setupCustomizations, withLegacyCloseContext } from "./formScripts";
import { dayjsLocal } from "./timezone";
import { __ } from "./translation";

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;
const YEAR = 365 * DAY;

// Studio portal, outside the desk SPA.
export const CUSTOMER_PORTAL_ROOT = "/help";

/**
 * @param {Object} config - Configuration object
 * @param {Ref<boolean>} config.isConfirmingDelete - Ref to track confirmation state
 * @param {Function} config.onConfirmDelete - Callback when delete is confirmed
 * @returns {Array} Array of option objects for use in dropdowns
 */
export function ConfirmDelete({ isConfirmingDelete, onConfirmDelete }) {
  return [
    {
      label: __("Delete"),
      icon: "lucide-trash-2",
      // preventDefault keeps the menu open so the confirm row can replace this one
      onClick: (event) => {
        event.preventDefault();
        isConfirmingDelete.value = true;
      },
      condition: () => !isConfirmingDelete.value,
    },
    {
      label: __("Confirm Delete"),
      icon: "lucide-trash-2",
      theme: "red",
      onClick: () => {
        onConfirmDelete();
        isConfirmingDelete.value = false;
      },
      condition: () => isConfirmingDelete.value,
    },
  ];
}

// Guests see quick links, so allow only paths, web and mail URLs.
export function isSafeLink(url: unknown) {
  return typeof url === "string" && /^(\/|https?:|mailto:)/i.test(url);
}

export function prettyDate(date) {
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

  // Return long format of time difference
  if (absDiff < 86400) {
    // Within a day — show sub-day granularity (past or future).
    if (absDiff < 60) return __("Just now");
    if (diff >= 0) {
      if (absDiff < 120) return __("1 minute ago");
      if (absDiff < 3600)
        return __("{0} minutes ago", [Math.floor(absDiff / 60)]);
      if (absDiff < 7200) return __("1 hour ago");
      return __("{0} hours ago", [Math.floor(absDiff / 3600)]);
    }
    if (absDiff < 120) return __("In 1 minute");
    if (absDiff < 3600)
      return __("In {0} minutes", [Math.floor(absDiff / 60)]);
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

export function timeAgo(date) {
  return prettyDate(date);
}

/**
 * The moment a server datetime names, for comparisons and durations. These do
 * not depend on the zone a date shows in, so skip `dayjsLocal`'s conversion:
 * it, and every later op on a zoned value, builds an `Intl` formatter.
 */
export function serverInstant(date: string) {
  const systemTimezone = getConfig("systemTimezone");
  if (!systemTimezone) return dayjs(date);
  return dayjs(dayjs.tz(date, systemTimezone).valueOf());
}

// Server rule: a milestone fails only when met after its due time.
export function isSlaMissed(metOn: string, due?: string | null) {
  return Boolean(due) && serverInstant(metOn).isAfter(serverInstant(due));
}

/** Format a duration using its two most significant units, e.g. "1d 9h" */
export function twoUnitDuration(milliseconds: number): string {
  const duration = dayjs.duration(milliseconds);

  const years = duration.years();
  const months = duration.months();
  const days = duration.days();
  const hours = duration.hours();
  const minutes = duration.minutes();
  const seconds = duration.seconds();

  if (years > 0) {
    return `${years}y ${months}mo`;
  } else if (months > 0) {
    return `${months}mo ${days}d`;
  } else if (days > 0) {
    return `${days}d ${hours}h`;
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`;
  }
  return `${seconds}s`;
}

export function isContentEmpty(content: string) {
  if (!content || content === null || content === undefined) {
    return true;
  }
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  if (doc.body.querySelector("img, video, iframe")) {
    return false;
  }
  return !doc.body.textContent?.trim();
}

// Keep plain-text newlines, which HTML would collapse.
export function plainTextToHtml(content: string) {
  const doc = new DOMParser().parseFromString(content || "", "text/html");
  if (doc.body.children.length) return content;
  return `<div class="whitespace-pre-wrap">${doc.body.innerHTML}</div>`;
}

// Heading ids only; article URLs take the server's `title_slug`.
function slugify(text = "") {
  return text
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .normalize("NFC")
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}]+/gu, "-")
    .replace(/^-|-$/g, "");
}

// Same ids on desk and portal so `#heading` links work; saved ids win.
export function addHeadingIds(html: string) {
  const doc = new DOMParser().parseFromString(html || "", "text/html");
  const used = new Set<string>();
  const headings = Array.from(
    doc.querySelectorAll("h1, h2, h3, h4, h5, h6")
  ).map((heading) => {
    const text = heading.textContent?.trim() || "";
    const base = heading.id || slugify(text) || "section";
    let id = base;
    for (let n = 2; used.has(id); n++) id = `${base}-${n}`;
    used.add(id);
    heading.id = id;
    return { id, text, level: Number(heading.tagName[1]) };
  });
  return { html: doc.body.innerHTML, headings };
}

// Scoped to the article: the icon sprite's <symbol>s reuse ids like `settings`.
export function findArticleHeading(id: string) {
  // `#` alone is not a selector: an article without headings asks for "".
  if (!id) return null;
  return document.querySelector<HTMLElement>(`.ProseMirror #${CSS.escape(id)}`);
}

// Lucide names are plain ASCII, so any emoji-presentation or pictographic
// character (or a variation selector, for keycaps like 1️⃣) means a legacy emoji.
export function isEmoji(str: string): boolean {
  return /\p{Emoji_Presentation}|\p{Extended_Pictographic}|\uFE0F/u.test(str);
}

/**
 * Compact relative duration between `target` and now, ignoring direction.
 * Examples: `1y`, `4 days 4h`, `2h 20m`, `5m`.
 */
export function shortDuration(target: string): string {
  const seconds = Math.abs(serverInstant(target).diff(dayjs(), "second"));
  if (seconds >= YEAR) {
    const years = Math.floor(seconds / YEAR);
    return countLabel(years, __("1 year"), __("{0} years"));
  }
  if (seconds >= MONTH) {
    const months = Math.floor(seconds / MONTH);
    return countLabel(months, __("1 month"), __("{0} months"));
  }
  if (seconds >= DAY) {
    const days = Math.floor(seconds / DAY);
    const hours = Math.floor((seconds % DAY) / HOUR);
    const dayLabel = countLabel(days, __("1 day"), __("{0} days"));
    return hours ? `${dayLabel} ${hours}h` : dayLabel;
  }
  if (seconds >= HOUR) {
    const hours = Math.floor(seconds / HOUR);
    const minutes = Math.floor((seconds % HOUR) / MINUTE);
    return minutes ? `${hours}h ${minutes}m` : `${hours}h`;
  }
  return `${Math.floor(seconds / MINUTE)}m`;
}

/**
 * Convert `link_filters` from the stored list format to the dict format that
 * `frappe.desk.search.search_link` expects.
 * @example
 * // in:  '[["User", "name", "in", ["a@x.com", "b@x.com"]]]'
 * // out: { name: ["in", ["a@x.com", "b@x.com"]] }
 */
export function parseLinkFilters(linkFilters: string) {
  const conditions = JSON.parse(linkFilters);
  if (!Array.isArray(conditions)) return conditions;
  return Object.fromEntries(
    conditions.map((condition) => {
      const [fieldname, operator, value] =
        condition.length === 4 ? condition.slice(1) : condition;
      return [fieldname, operator === "=" ? value : [operator, value]];
    })
  );
}

type DropdownOption = { label: string; value: string | number };

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

export function getErrorMessage(
  error: any,
  showToast: boolean = false,
  fallback: string = ""
): string {
  const msg = error?.messages?.join(", ") || error?.message || fallback;
  if (showToast) {
    toast.error(msg);
  }
  return msg;
}

export function handleInviteUserSuccess(
  data: Record<
    | "disabled_user_emails"
    | "accepted_invite_emails"
    | "pending_invite_emails"
    | "invited_emails",
    string[]
  >
) {
  const list = (emails: string[]) => emails.join(", ");
  if (data.invited_emails.length)
    toast.success(__("{0} invited successfully", list(data.invited_emails)));
  if (data.disabled_user_emails.length)
    toast.info(
      __("{0} already present and disabled", list(data.disabled_user_emails))
    );
  if (data.pending_invite_emails.length)
    toast.info(__("{0} already invited", list(data.pending_invite_emails)));
  if (data.accepted_invite_emails.length)
    toast.info(__("{0} already present", list(data.accepted_invite_emails)));
}

export const SEARCH_DEBOUNCE_MS = 300;

// Mirrors frappe.handler.ALLOWED_MIMETYPES, which the server enforces for users without desk access.
const CUSTOMER_FILE_TYPES = [
  ".png",
  ".jpg",
  ".jpeg",
  ".gif",
  ".pdf",
  ".txt",
  ".csv",
  ".mov",
  ".mp4",
  ".doc",
  ".docx",
  ".xls",
  ".xlsx",
  ".odt",
  ".ods",
];

// Undefined for agents, who may upload anything.
export function uploadableFileTypes(isAgent: boolean) {
  return isAgent ? undefined : CUSTOMER_FILE_TYPES;
}

export const DATE_FORMATS = {
  clock: "h:mm A",
  short: "D MMM YYYY",
  step: "ddd D MMM, h:mm A",
};

export function parseJson(value: unknown, fallback: any = undefined) {
  if (!value) return fallback;
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value) ?? fallback;
  } catch {
    return fallback;
  }
}

export type ActionOptions = {
  busy?: Ref<boolean>;
  success?: string;
  fallback: string;
};

export async function runAction(
  action: () => Promise<unknown>,
  options: ActionOptions
) {
  const { busy, success, fallback } = options;
  if (busy?.value) return;
  if (busy) busy.value = true;
  try {
    await action();
    if (success) toast.success(success);
    return true;
  } catch (error) {
    console.error(error);
    getErrorMessage(error, true, fallback);
  } finally {
    if (busy) busy.value = false;
  }
}

export function setValues(
  doctype: string,
  name: string,
  values: Record<string, unknown>
) {
  return call("frappe.client.set_value", { doctype, name, fieldname: values });
}

// Form script actions call `close()` or `close.close()`, as on the desk.
function scriptDialog({ title, message, size, icon, actions }) {
  return dialog.confirm({
    title,
    message,
    size,
    icon,
    actions: withLegacyCloseContext(actions),
  });
}

// The desk's context, so existing scripts keep working.
export async function runFormScripts(
  data,
  context,
  extra: Record<string, unknown> = {}
) {
  await setupCustomizations(data, {
    call: context.call,
    router: context.router,
    $dialog: scriptDialog,
    ...extra,
  });
  return data._customActions || [];
}

export function askConfirm({ title, message, label, theme, action }) {
  return dialog.confirm({
    title,
    message,
    theme,
    confirmLabel: label,
    cancelLabel: __("Cancel"),
    onConfirm: action,
  });
}

export function updateTicket(name: string, values: Record<string, unknown>) {
  return setValues("HD Ticket", name, values);
}

// Args already went through `__()`, so the extractor sees the literals.
export function countLabel(count: number, singular: string, plural: string) {
  return count === 1 ? singular : plural.replace("{0}", String(count));
}

// "Category · 3 min read"; either part may be missing.
export function articleMeta(categoryName?: string, minutes?: number) {
  const readTime = minutes
    ? countLabel(minutes, __("1 min read"), __("{0} min read"))
    : "";
  return [categoryName, readTime].filter(Boolean).join(" · ");
}

// `legacy`: execCommand fallback where the Clipboard API is missing (plain http).
export async function copyToClipboard(
  text: string,
  message: string = __("Copied to clipboard.")
) {
  await useClipboard({ legacy: true }).copy(text);
  toast.success(message);
}

export function copyPageLink() {
  return copyToClipboard(window.location.href, __("Link copied"));
}

export function matchesQuery(query: string, ...fields: (string | undefined)[]) {
  const needle = query.trim().toLowerCase();
  return !needle || fields.join(" ").toLowerCase().includes(needle);
}
