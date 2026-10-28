import { SlaValidationErrors } from "@/components/Settings/Sla/types";
import { __ } from "@/translation";
import type { HDServiceDay } from "@/types/doctypes";
import { validateConditions } from "@/utils";
import { ref } from "vue";

/** Fresh rows each call, so edits to one new policy never leak into the next. */
const getDefaultSupportAndResolution = () =>
  ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].map((workday) => ({
    workday,
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  }));

export const slaData = ref({
  name: "",
  service_level: "",
  description: "",
  enabled: true,
  default_sla: false,
  rank: 0,
  apply_sla_for_resolution: true,
  priorities: [],
  holiday_list: "Default",
  default_priority: "",
  start_date: "",
  end_date: "",
  loading: false,
  support_and_resolution: getDefaultSupportAndResolution(),
  default_ticket_status: "",
  reopen_ticket_status: "",
  condition: [],
  condition_json: [],
});

export const resetSlaData = () => {
  slaData.value = {
    name: "",
    service_level: "",
    description: "",
    enabled: true,
    default_sla: false,
    rank: 0,
    apply_sla_for_resolution: true,
    priorities: [],
    holiday_list: "Default",
    default_priority: "",
    start_date: "",
    end_date: "",
    loading: false,
    support_and_resolution: getDefaultSupportAndResolution(),
    default_ticket_status: "",
    reopen_ticket_status: "",
    condition: [],
    condition_json: [],
  };
};

export const slaActiveScreen = ref<{
  screen: "list" | "view";
  data: Record<string, any> | null;
  fetchData: boolean;
}>({ screen: "list", data: null, fetchData: true });

export const slaDataErrors = ref<SlaValidationErrors>({
  service_level: "",
  description: "",
  enabled: "",
  default_sla: "",
  apply_sla_for_resolution: "",
  priorities: "",
  holiday_list: "",
  default_priority: "",
  start_date: "",
  end_date: "",
  support_and_resolution: "",
  condition: "",
});

export const resetSlaDataErrors = () => {
  slaDataErrors.value = {
    service_level: "",
    description: "",
    enabled: "",
    default_sla: "",
    apply_sla_for_resolution: "",
    priorities: "",
    holiday_list: "",
    default_priority: "",
    start_date: "",
    end_date: "",
    support_and_resolution: "",
    condition: "",
  };
};

type SlaField = keyof SlaValidationErrors;

export function validateSlaData(
  key?: SlaField,
  skipConditionCheck = false
): SlaValidationErrors {
  // Reset all errors
  resetSlaDataErrors();

  const validateField = (field: SlaField) => {
    if (key && field !== key) return;

    switch (field) {
      case "service_level":
        if (!slaData.value.service_level?.trim()) {
          slaDataErrors.value.service_level = __("SLA policy name is required.");
        } else {
          slaDataErrors.value.service_level = "";
        }
        break;
      case "priorities":
        if (
          !Array.isArray(slaData.value.priorities) ||
          slaData.value.priorities.length === 0
        ) {
          slaDataErrors.value.priorities = __("At least one priority is required.");
        } else {
          const prioritiesError: string[] = [];
          slaData.value.priorities.forEach((priority, index) => {
            const priorityNum = index + 1;
            if (!priority.priority?.trim()) {
              prioritiesError.push(
                `Priority ${priorityNum}: Priority name is required.`
              );
            }
            if (!priority.response_time || priority.response_time == 0) {
              prioritiesError.push(
                `Priority ${priorityNum}: Response time is required.`
              );
            }
            if (Boolean(slaData.value.apply_sla_for_resolution)) {
              if (!priority.resolution_time || priority.resolution_time == 0) {
                prioritiesError.push(
                  `Priority ${priorityNum}: Resolution time is required.`
                );
              }
            }
            if (
              priority.response_time > priority.resolution_time &&
              Boolean(slaData.value.apply_sla_for_resolution)
            ) {
              prioritiesError.push(
                `Priority ${priorityNum}: Response time cannot be greater than resolution time.`
              );
            }
          });

          // Check for duplicate priorities
          const priorityNames = slaData.value.priorities
            .map((p) => p.priority?.trim().toLowerCase())
            .filter(Boolean);
          const uniquePriorities = new Set(priorityNames);

          if (priorityNames.length !== uniquePriorities.size) {
            prioritiesError.push("Priorities must be unique");
          }

          if (prioritiesError.length > 0) {
            slaDataErrors.value.priorities = prioritiesError.join(", ");
          } else {
            slaDataErrors.value.priorities = "";
          }

          const hasDefaultPriority = slaData.value.priorities.some((p) =>
            Boolean(p.default_priority)
          );
          if (!hasDefaultPriority) {
            slaDataErrors.value.default_priority =
              "Default priority is required";
          } else {
            slaDataErrors.value.default_priority = "";
          }
        }
        break;
      case "holiday_list":
        if (!slaData.value.holiday_list) {
          slaDataErrors.value.holiday_list = "Holiday list is required.";
        } else {
          slaDataErrors.value.holiday_list = "";
        }
        break;
      case "start_date":
        if (
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.start_date =
            "Start date cannot be after end date.";
        } else {
          slaDataErrors.value.start_date = "";
        }
        break;
      case "end_date":
        if (
          slaData.value.end_date &&
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.end_date = "End date cannot be before start date.";
        } else {
          slaDataErrors.value.end_date = "";
        }
        break;
      case "condition":
        if (skipConditionCheck) {
          break;
        }
        if (
          slaData.value.condition_json.length > 0 &&
          !validateConditions(slaData.value.condition_json)
        ) {
          slaDataErrors.value.condition = "Valid conditions are required.";
        } else {
          slaDataErrors.value.condition = "";
        }
        break;
      case "support_and_resolution":
        const validWorkdays = slaData.value.support_and_resolution?.filter(
          (day) =>
            day.workday &&
            day.workday.trim() !== "" &&
            day.start_time &&
            day.end_time &&
            day.start_time.trim() !== "" &&
            day.end_time.trim() !== ""
        );

        if (!validWorkdays?.length) {
          slaDataErrors.value.support_and_resolution =
            "At least one valid workday with workday, start time, and end time is required.";
        } else {
          // Check for duplicate workdays
          const workdayMap = new Map();
          const duplicateWorkdays = [];

          for (const day of validWorkdays) {
            if (workdayMap.has(day.workday)) {
              duplicateWorkdays.push(day.workday);
            } else {
              workdayMap.set(day.workday, true);
            }
          }

          if (duplicateWorkdays.length > 0) {
            slaDataErrors.value.support_and_resolution = `Duplicate workday found: ${duplicateWorkdays.join(
              ", "
            )}. Each workday should be unique.`;
            return slaDataErrors.value;
          } else {
            slaDataErrors.value.support_and_resolution = "";
          }

          const invalidTimeRanges = [];
          for (const day of validWorkdays) {
            const startTimeStr = day.start_time.trim();
            const endTimeStr = day.end_time.trim();

            if (toMinutes(startTimeStr) >= toMinutes(endTimeStr)) {
              invalidTimeRanges.push(
                `${day.workday} (${startTimeStr} - ${endTimeStr})`
              );
            }
          }

          const invalidBreaks = slaData.value.support_and_resolution
            .filter((day) => getBreakError(day))
            .map((day) => `${day.workday}: ${getBreakError(day)}`);

          if (invalidTimeRanges.length > 0) {
            slaDataErrors.value.support_and_resolution = `End time must be after start time for: ${invalidTimeRanges.join(
              ", "
            )}`;
          } else if (invalidBreaks.length > 0) {
            slaDataErrors.value.support_and_resolution =
              invalidBreaks.join(" ");
          } else {
            slaDataErrors.value.support_and_resolution = "";
          }
        }
        break;

      default:
        break;
    }
  };

  if (key) {
    validateField(key);
  } else {
    (Object.keys(slaDataErrors.value) as SlaField[]).forEach(validateField);
  }

  return slaDataErrors.value;
}

/** Why a workday's break is invalid, or "" when it is valid or there is none. */
export function getBreakError(
  day: Partial<
    Pick<HDServiceDay, "start_time" | "end_time" | "break_start" | "break_end">
  >
): string {
  if (!day.break_start && !day.break_end) return "";
  if (!day.break_start || !day.break_end) {
    return __("Set both break start and break end, or neither.");
  }
  const [start, end, breakStart, breakEnd] = [
    day.start_time,
    day.end_time,
    day.break_start,
    day.break_end,
  ].map(toMinutes);
  if (breakEnd <= breakStart) return __("Break end must be after break start.");
  if (breakStart <= start || breakEnd >= end) {
    return __("Break must be within working hours.");
  }
  return "";
}

/** Minutes since midnight for an "H:MM" or "H:MM:SS" time. */
export function toMinutes(time?: string | null): number {
  const [hours, minutes] = (time || "").split(":").map(Number);
  return (hours || 0) * 60 + (minutes || 0);
}
