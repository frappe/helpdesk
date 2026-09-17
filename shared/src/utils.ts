import { dayjs, dayjsLocal } from "frappe-ui";

import { __ } from "./translation";

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;
const YEAR = 365 * DAY;

export function validateEmail(email) {
  const regExp =
    /^((?:"[\p{L}\p{M}\d .,_%+-]+"|[\p{L}\d._%+-]+)\s)?<([\p{L}\d._%+-]+@[\p{L}\d.-]+\.[\p{L}]{2,})>$|^([\p{L}\d._%+-]+@[\p{L}\d.-]+\.[\p{L}]{2,})$/u;
  return regExp.test(email);
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
}

export function timeAgo(date) {
  return prettyDate(date);
}

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
