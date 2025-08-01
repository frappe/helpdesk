import { validateConditions } from "@/utils";
import { ref } from "vue";

const defaultAssignmentDays = [
  {
    day: "Monday",
  },
  {
    day: "Tuesday",
  },
  {
    day: "Wednesday",
  },
  {
    day: "Thursday",
  },
  {
    day: "Friday",
  },
  {
    day: "Saturday",
  },
  {
    day: "Sunday",
  },
];

export const assignmentRuleData = ref<Record<string, any> | null>({
  loading: false,
  assign_condition: "",
  unassign_condition: "",
  assign_condition_json: [],
  unassign_condition_json: [],
  rule: "Round Robin",
  priority: 1,
  users: [],
  disabled: true,
  description: "",
  name: "",
  assignment_rule_name: "",
  assignment_days: defaultAssignmentDays,
});

export const resetAssignmentRuleData = () => {
  assignmentRuleData.value = {
    loading: false,
    assign_condition: "",
    unassign_condition: "",
    assign_condition_json: [],
    unassign_condition_json: [],
    rule: "Round Robin",
    priority: 1,
    users: [],
    disabled: true,
    description: "",
    name: "",
    assignment_rule_name: "",
    assignment_days: defaultAssignmentDays,
  };
};

export const assignmentRulesActiveScreen = ref<{
  screen: "list" | "view";
  data: Record<string, any> | null;
}>({ screen: "list", data: null });

export const validateAssignmentRule = (
  key?: string,
  skipConditionCheck = false
) => {
  const validateField = (field: string) => {
    if (key && field !== key) return;

    switch (field) {
      case "assignment_rule_name":
        assignmentRulesErrors.value.assignment_rule_name =
          assignmentRuleData.value.assignment_rule_name?.length > 0
            ? ""
            : "Name is required";
        break;
      case "description":
        assignmentRulesErrors.value.description =
          assignmentRuleData.value.description?.length > 0
            ? ""
            : "Description is required";
        break;
      case "assign_condition":
        if (skipConditionCheck) {
          break;
        }
        assignmentRulesErrors.value.assign_condition =
          assignmentRuleData.value.assign_condition_json?.length > 0
            ? ""
            : "Assign condition is required";

        if (
          !validateConditions(assignmentRuleData.value.assign_condition_json)
        ) {
          assignmentRulesErrors.value.assign_condition_error =
            "Assign conditions are invalid";
        } else {
          assignmentRulesErrors.value.assign_condition_error = "";
        }

        break;
      case "unassign_condition":
        if (skipConditionCheck) {
          break;
        }
        if (
          !validateConditions(assignmentRuleData.value.unassign_condition_json)
        ) {
          assignmentRulesErrors.value.unassign_condition_error =
            "Unassign conditions are invalid";
        } else {
          assignmentRulesErrors.value.unassign_condition_error = "";
        }
        break;
      case "users":
        assignmentRulesErrors.value.users =
          assignmentRuleData.value.users?.length > 0
            ? ""
            : "Users are required";
        break;
      case "assignment_days":
        assignmentRulesErrors.value.assignment_days =
          assignmentRuleData.value.assignment_days?.length > 0
            ? ""
            : "Assignment days are required";
        break;
      default:
        break;
    }
  };

  if (key) {
    validateField(key);
  } else {
    (Object.keys(assignmentRulesErrors.value) as string[]).forEach(
      validateField
    );
  }

  return assignmentRulesErrors.value;
};

export const assignmentRulesErrors = ref<Record<string, any> | null>({
  assignment_rule_name: "",
  assign_condition: "",
  assign_condition_error: "",
  unassign_condition_error: "",
  users: "",
  description: "",
  assignment_days: "",
});

export const resetAssignmentRuleErrors = () => {
  (Object.keys(assignmentRulesErrors.value) as string[]).forEach((key) => {
    assignmentRulesErrors.value[key] = "";
  });
};
