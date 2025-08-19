import { SlaValidationErrors } from "@/components/Settings/Sla/types";
import { validateConditions } from "@/utils";
import { ref } from "vue";

const defaultStatus = [
  {
    status: "Replied",
    sla_behavior: "Paused",
  },
  {
    status: "Closed",
    sla_behavior: "Fulfilled",
  },
  {
    status: "Resolved",
    sla_behavior: "Fulfilled",
  },
];

const defaultSupportAndResolution = [
  {
    workday: "Monday",
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  },
  {
    workday: "Tuesday",
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  },
  {
    workday: "Wednesday",
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  },
  {
    workday: "Thursday",
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  },
  {
    workday: "Friday",
    start_time: "09:00:00",
    end_time: "17:00:00",
    id: Math.random().toString(36).substring(2, 9),
  },
];

export const slaData = ref({
  name: "",
  service_level: "",
  description: "",
  enabled: false,
  default_sla: false,
  apply_sla_for_resolution: true,
  priorities: [],
  statuses: defaultStatus,
  holiday_list: "Default",
  default_priority: "",
  start_date: "",
  end_date: "",
  loading: false,
  support_and_resolution: defaultSupportAndResolution,
  condition: [],
  condition_json: [],
});

export const resetSlaData = () => {
  slaData.value = {
    name: "",
    service_level: "",
    description: "",
    enabled: false,
    default_sla: false,
    apply_sla_for_resolution: true,
    priorities: [],
    statuses: defaultStatus,
    holiday_list: "Default",
    default_priority: "",
    start_date: "",
    end_date: "",
    loading: false,
    support_and_resolution: defaultSupportAndResolution,
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
  statuses: "",
  statuses_conflict: "",
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
    statuses: "",
    statuses_conflict: "",
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
          slaDataErrors.value.service_level = "SLA policy name is required";
        } else {
          slaDataErrors.value.service_level = "";
        }
        break;
      case "priorities":
        if (
          !Array.isArray(slaData.value.priorities) ||
          slaData.value.priorities.length === 0
        ) {
          slaDataErrors.value.priorities = "At least one priority is required";
        } else {
          const prioritiesError: string[] = [];
          slaData.value.priorities.forEach((priority, index) => {
            const priorityNum = index + 1;
            if (!priority.priority?.trim()) {
              prioritiesError.push(
                `Priority ${priorityNum}: Priority name is required`
              );
            }
            if (!priority.response_time || priority.response_time == 0) {
              prioritiesError.push(
                `Priority ${priorityNum}: Response time is required`
              );
            }
            if (Boolean(slaData.value.apply_sla_for_resolution)) {
              if (!priority.resolution_time || priority.resolution_time == 0) {
                prioritiesError.push(
                  `Priority ${priorityNum}: Resolution time is required`
                );
              }
            }
            if (
              priority.response_time > priority.resolution_time &&
              Boolean(slaData.value.apply_sla_for_resolution)
            ) {
              prioritiesError.push(
                `Priority ${priorityNum}: Response time cannot be greater than resolution time`
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
      case "statuses":
        if (
          !Array.isArray(slaData.value.statuses) ||
          slaData.value.statuses.length === 0
        ) {
          slaDataErrors.value.statuses =
            "At least one status for 'Fulfilled on' and 'Paused on' is required";
        } else {
          const hasFulfilled = slaData.value.statuses.some(
            (s) => s.sla_behavior === "Fulfilled"
          );
          const hasPaused = slaData.value.statuses.some(
            (s) => s.sla_behavior === "Paused"
          );

          if (!hasFulfilled) {
            slaDataErrors.value.statuses =
              "At least one 'Fulfilled on' status is required";
          }
          if (!hasPaused) {
            slaDataErrors.value.statuses =
              "At least one 'Paused on' status is required";
          }
          if (hasFulfilled && hasPaused) {
            slaDataErrors.value.statuses = "";
          }

          // Check for duplicate statuses and ensure each status has only one behavior
          const statusMap = new Map();
          const duplicateStatuses = [];
          const conflictingBehaviors = [];

          for (const status of slaData.value.statuses) {
            const statusKey = status.status?.trim().toLowerCase();
            const behavior = status.sla_behavior;

            if (!statusMap.has(statusKey)) {
              statusMap.set(statusKey, new Set([behavior]));
            } else {
              // Check if this status already has this behavior
              if (statusMap.get(statusKey).has(behavior)) {
                duplicateStatuses.push(status.status);
              } else {
                // This status has a different behavior already
                conflictingBehaviors.push({
                  status: status.status,
                  behaviors: [...statusMap.get(statusKey), behavior],
                });
                statusMap.get(statusKey).add(behavior);
              }
            }
          }

          const errorMessages = [];
          if (duplicateStatuses.length > 0) {
            errorMessages.push(
              `Duplicate status behavior found for: ${[
                ...new Set(duplicateStatuses),
              ].join(", ")}`
            );
          }
          if (conflictingBehaviors.length > 0) {
            const conflictMessages = conflictingBehaviors.map(
              ({ status, behaviors }) =>
                `"${status}" cannot be both ${behaviors.join(" and ")}`
            );
            errorMessages.push(
              `Conflicting behaviors: ${conflictMessages.join("; ")}`
            );
          }

          if (errorMessages.length > 0) {
            slaDataErrors.value.statuses_conflict = errorMessages.join(". ");
          } else {
            slaDataErrors.value.statuses_conflict = "";
          }
        }
        break;
      case "holiday_list":
        if (!slaData.value.holiday_list) {
          slaDataErrors.value.holiday_list = "Holiday list is required";
        } else {
          slaDataErrors.value.holiday_list = "";
        }
        break;
      case "start_date":
        if (
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.start_date =
            "Start date cannot be after end date";
        } else {
          slaDataErrors.value.start_date = "";
        }
        break;
      case "end_date":
        if (
          slaData.value.end_date &&
          new Date(slaData.value.end_date) < new Date(slaData.value.start_date)
        ) {
          slaDataErrors.value.end_date = "End date cannot be before start date";
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
          slaDataErrors.value.condition = "Valid conditions are required";
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
            "At least one valid workday with workday, start time, and end time is required";
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

            const parseTime = (timeStr: string) => {
              const [hours, minutes] = timeStr.split(":").map(Number);
              const date = new Date();
              date.setHours(hours, minutes || 0, 0, 0);
              return date;
            };

            try {
              const startTime = parseTime(startTimeStr);
              const endTime = parseTime(endTimeStr);

              if (startTime >= endTime) {
                invalidTimeRanges.push(
                  `${day.workday} (${startTimeStr} - ${endTimeStr})`
                );
              }
            } catch (error) {
              // If time parsing fails, mark as invalid
              invalidTimeRanges.push(`${day.workday} (Invalid time format)`);
            }
          }

          if (invalidTimeRanges.length > 0) {
            slaDataErrors.value.support_and_resolution = `End time must be after start time for: ${invalidTimeRanges.join(
              ", "
            )}`;
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
