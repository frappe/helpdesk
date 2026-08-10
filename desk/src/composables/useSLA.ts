import { dayjs } from "frappe-ui";
import { computed, type ComputedRef, type Ref } from "vue";

export type SLAState = "due" | "fulfilled" | "overdue" | "failed" | "hold";

export interface SLAMetric {
  state: SLAState;
  /** Short display value, e.g. "2d 4h", "Overdue by 59m", "On Hold" */
  value: string;
  color: "orange" | "green" | "red" | "blue" | "violet";
  /** Empty when the SLA target was never set or was cleared on pause */
  dueBy: string;
  /** When the SLA was actually met: first_responded_on / resolution_date */
  actual: string;
  /** How late, e.g. "+59m" — set for overdue and failed states */
  delay: string;
  /** True when delay comes from the SLA engine and counts working hours only */
  delayInWorkingHours?: boolean;
  /** Wall-clock delay, shown alongside the working-hours delay */
  calendarDelay?: string;
  /** How long the metric took when fulfilled, e.g. "3h 20m" */
  fulfilledIn?: string;
}

interface TicketLike {
  doc?: Record<string, any>;
}

const inkClasses: Record<SLAMetric["color"], string> = {
  orange: "text-ink-amber-8",
  green: "text-ink-green-8",
  red: "text-ink-red-7",
  blue: "text-ink-blue-8",
  violet: "text-ink-violet-8",
};

// "Due" is the resting state of every open ticket, so it stays gray; colour
// only appears when something changed (fulfilled, overdue, failed, hold).
export function slaTextColor(metric: SLAMetric): string {
  return metric.state === "due" ? "text-ink-gray-7" : inkClasses[metric.color];
}

/** Display text, e.g. "Fulfilled in 3h 20m", "Due in 2d 4h", "On Hold" */
export function slaLabel(metric: SLAMetric): string {
  if (metric.state !== "fulfilled") return metric.value;
  return metric.fulfilledIn
    ? `Fulfilled in ${metric.fulfilledIn}`
    : "Fulfilled";
}

export function useSLA(ticket: Ref<TicketLike | null | undefined>): {
  firstResponse: ComputedRef<SLAMetric | null>;
  resolution: ComputedRef<SLAMetric | null>;
} {
  const doc = computed(() => ticket.value?.doc ?? {});

  // Cases:
  // - responded before due (or with no recorded due date) -> fulfilled
  // - responded after due -> failed
  // - not responded, due in future -> due
  // - not responded, due in past -> overdue
  // - no policy -> null (card hidden), whether it never had one or was detached
  const firstResponse = computed<SLAMetric | null>(() => {
    const d = doc.value;
    if (!d.sla) return null; // nothing promised, so nothing to report against

    if (d.first_responded_on) {
      const inTime =
        !d.response_by ||
        dayjs(d.first_responded_on).isBefore(dayjs(d.response_by));
      if (inTime) {
        return {
          ...metric("fulfilled", "", "green", {
            dueBy: d.response_by,
            actual: d.first_responded_on,
          }),
          fulfilledIn: d.first_response_time
            ? twoUnitDuration(d.first_response_time * 1000)
            : shortDuration(d.first_responded_on, d.creation),
        };
      }
      const failed = d.first_response_failed_by
        ? twoUnitDuration(d.first_response_failed_by * 1000)
        : shortDuration(d.first_responded_on, d.response_by);
      return {
        ...metric("failed", `Failed by ${failed}`, "red", {
          dueBy: d.response_by,
          actual: d.first_responded_on,
          delay: `+${failed}`,
        }),
        delayInWorkingHours: Boolean(d.first_response_failed_by),
        calendarDelay: d.first_response_failed_by
          ? shortDuration(d.first_responded_on, d.response_by)
          : undefined,
      };
    }

    if (!d.response_by) return null;

    if (dayjs().isBefore(dayjs(d.response_by))) {
      return metric(
        "due",
        `Due in ${coarseDuration(d.response_by)}`,
        "orange",
        {
          dueBy: d.response_by,
        }
      );
    }
    const overdue = coarseDuration(d.response_by);
    return metric("overdue", `Overdue by ${overdue}`, "red", {
      dueBy: d.response_by,
      delay: `+${overdue}`,
    });
  });

  // Same cases as first response, plus:
  // - paused before the deadline -> hold (pausing clears resolution_by, so an
  //   empty target while paused still means hold, not "no SLA")
  const resolution = computed<SLAMetric | null>(() => {
    const d = doc.value;
    if (!d.sla) return null;

    const pausedBeforeBreach =
      !d.resolution_by ||
      dayjs(d.resolution_by).isAfter(dayjs(d.on_hold_since));
    if (
      d.status_category === "Paused" &&
      d.on_hold_since &&
      pausedBeforeBreach
    ) {
      return metric("hold", "On Hold", "blue", { dueBy: d.resolution_by });
    }

    if (d.resolution_date) {
      const inTime =
        !d.resolution_by ||
        dayjs(d.resolution_date).isBefore(dayjs(d.resolution_by));
      if (inTime) {
        return {
          ...metric("fulfilled", "", "green", {
            dueBy: d.resolution_by,
            actual: d.resolution_date,
          }),
          fulfilledIn: d.resolution_time
            ? twoUnitDuration(d.resolution_time * 1000)
            : shortDuration(d.resolution_date, d.creation),
        };
      }
      const failed = d.resolution_failed_by
        ? twoUnitDuration(d.resolution_failed_by * 1000)
        : shortDuration(d.resolution_date, d.resolution_by);
      return {
        ...metric("failed", `Failed by ${failed}`, "red", {
          dueBy: d.resolution_by,
          actual: d.resolution_date,
          delay: `+${failed}`,
        }),
        delayInWorkingHours: Boolean(d.resolution_failed_by),
        calendarDelay: d.resolution_failed_by
          ? shortDuration(d.resolution_date, d.resolution_by)
          : undefined,
      };
    }

    if (!d.resolution_by) return null;

    if (dayjs().isBefore(dayjs(d.resolution_by))) {
      return metric(
        "due",
        `Due in ${coarseDuration(d.resolution_by)}`,
        "violet",
        { dueBy: d.resolution_by }
      );
    }
    const overdue = coarseDuration(d.resolution_by);
    return metric("overdue", `Overdue by ${overdue}`, "red", {
      dueBy: d.resolution_by,
      delay: `+${overdue}`,
    });
  });

  return { firstResponse, resolution };
}

function metric(
  state: SLAState,
  value: string,
  color: SLAMetric["color"],
  extra: Partial<Pick<SLAMetric, "dueBy" | "actual" | "delay">>
): SLAMetric {
  return {
    state,
    value,
    color,
    dueBy: extra.dueBy || "",
    actual: extra.actual || "",
    delay: extra.delay || "",
  };
}

function shortDuration(date: string, end?: string): string {
  if (!end) {
    end = dayjs().toString();
  }
  return twoUnitDuration(dayjs(date).diff(dayjs(end)));
}

/** Distance from now in whole minutes. Countdown values ("Due in",
 * "Overdue by") don't tick, so seconds would read as a frozen timer. */
function coarseDuration(date: string): string {
  const diff = dayjs(date).startOf("minute").diff(dayjs().startOf("minute"));
  return twoUnitDuration(Math.abs(diff));
}

/** Format a duration using its two most significant units, e.g. "1d 9h" */
function twoUnitDuration(milliseconds: number): string {
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
