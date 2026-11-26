import { __ } from "@/translation";
import { getDateFormat } from "@/utils";
import { serverInstant } from "@helpdesk/shared/utils";
import { dayjs, dayjsLocal, type Dayjs } from "frappe-ui";
import calendar from "dayjs/plugin/calendar";

dayjs.extend(calendar);

export interface ExpiryPreset {
  label: string;
  short: string;
  /** Null means the status never clears. */
  expiresOn: () => Dayjs | null;
  never?: true;
}

const TIME_FORMAT = "h:mm A";

// a function so the labels translate at render
export function expiryPresets(): ExpiryPreset[] {
  const after = (amount: number, unit: "minute" | "hour") => () =>
    dayjsLocal().add(amount, unit);
  return [
    { label: __("30 minutes"), short: "30m", expiresOn: after(30, "minute") },
    { label: __("1 hour"), short: "1h", expiresOn: after(1, "hour") },
    { label: __("4 hours"), short: "4h", expiresOn: after(4, "hour") },
    {
      label: __("Today"),
      short: __("Today"),
      expiresOn: () => dayjsLocal().endOf("day"),
    },
    {
      label: __("This week"),
      short: __("Week"),
      expiresOn: () => dayjsLocal().endOf("week"),
    },
    {
      label: __("Never"),
      short: __("Never"),
      never: true,
      expiresOn: () => null,
    },
  ];
}

export function expiryLabel(expiresOn: string): string {
  if (!expiresOn) return "";
  const local = dayjsLocal(expiresOn);
  const date = getDateFormat();
  return local.calendar(dayjsLocal(), {
    sameDay: TIME_FORMAT,
    nextDay: `[${__("Tomorrow")}] ${TIME_FORMAT}`,
    nextWeek: `ddd ${TIME_FORMAT}`,
    sameElse: date,
    lastDay: date,
    lastWeek: date,
  });
}

export function expiryRemaining(expiresOn: string, now: Date): string {
  if (!expiresOn) return "";
  // rounded, so a fresh 1h reads "1h", not "59m"
  const minutes = Math.round(
    serverInstant(expiresOn).diff(now, "minute", true)
  );
  if (minutes < 1) return __("<1m");
  const left = dayjs.duration(minutes, "minute");
  const days = Math.floor(left.asDays());
  const parts = days
    ? [`${days}d`, left.hours() && `${left.hours()}h`]
    : [
        left.hours() && `${left.hours()}h`,
        left.minutes() && `${left.minutes()}m`,
      ];
  return parts.filter(Boolean).join(" ");
}
