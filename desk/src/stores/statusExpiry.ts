import { __ } from "@/translation";
import { serverInstant } from "@helpdesk/shared/utils";
import { dayjs, dayjsLocal, type Dayjs } from "frappe-ui";
import calendar from "dayjs/plugin/calendar";

dayjs.extend(calendar);

export interface ExpiryPreset {
  label: string;
  /** Chip form: "30m". */
  short: string;
  /** Null means the status never clears. */
  expiresOn: () => Dayjs | null;
  never?: true;
}

// 12-hour, e.g. "9:41 AM"
const TIME_FORMAT = "h:mm A";

/** "Clear after" choices. A function so labels translate at render. */
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
      short: __("This week"),
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

/** Button text for a system-time expiry, on the agent's clock:
 * "9:41 AM", "Tomorrow 9:41 AM", "Thu 9:41 AM", "30 Oct". */
export function expiryLabel(expiresOn: string): string {
  if (!expiresOn) return "";
  const local = dayjsLocal(expiresOn);
  const date = dateFormat(local);
  return local.calendar(dayjsLocal(), {
    sameDay: TIME_FORMAT,
    nextDay: `[${__("Tomorrow")}] ${TIME_FORMAT}`,
    nextWeek: `ddd ${TIME_FORMAT}`,
    sameElse: date,
    lastDay: date,
    lastWeek: date,
  });
}

/** Sentence form: "Clears today at 9:41 AM", "Clears on 30 Oct at 9:41 AM". */
export function expirySummary(expiresOn: string): string {
  if (!expiresOn) return __("Clear status after");
  const local = dayjsLocal(expiresOn);
  const time = local.format(TIME_FORMAT);
  const onDate = () =>
    __("Clears on {0} at {1}", [local.format(dateFormat(local)), time]);
  return local.calendar(dayjsLocal(), {
    sameDay: () => __("Clears today at {0}", [time]),
    nextDay: () => __("Clears tomorrow at {0}", [time]),
    nextWeek: () => __("Clears {0} at {1}", [local.format("dddd"), time]),
    sameElse: onDate,
    lastDay: onDate,
    lastWeek: onDate,
  });
}

/** Time left until a system-time expiry: "42m", "3h 12m", "2d 4h". */
export function expiryRemaining(expiresOn: string, now: Date): string {
  if (!expiresOn) return "";
  // rounded, so a fresh 1h reads "1h", not "59m"
  const minutes = Math.round(
    serverInstant(expiresOn).diff(now, "minute", true)
  );
  if (minutes < 1) return __("<1m");
  // dayjs splits the units; it has no compact "2d 4h" format, so join here
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

// the year only when it is not this one
function dateFormat(local: Dayjs): string {
  return local.isSame(dayjsLocal(), "year") ? "D MMM" : "D MMM YYYY";
}
