import { validateConditions } from "@/utils";
import { ref } from "vue";

const defaultAssignmentDays = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

export const assignmentRuleData = ref<Record<string, any> | null>({
  assignCondition: "",
  unassignCondition: "",
  assignConditionJson: [],
  unassignConditionJson: [],
  rule: "Round Robin",
  priority: 1,
  users: [],
  disabled: false,
  description: "",
  name: "",
  assignmentRuleName: "",
  assignmentDays: defaultAssignmentDays,
});

export const resetAssignmentRuleData = () => {
  assignmentRuleData.value = {
    assignCondition: "",
    unassignCondition: "",
    assignConditionJson: [],
    unassignConditionJson: [],
    rule: "Round Robin",
    priority: 1,
    users: [],
    disabled: false,
    description: "",
    name: "",
    assignmentRuleName: "",
    assignmentDays: defaultAssignmentDays,
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
      case "assignmentRuleName":
        if (assignmentRuleData.value.assignmentRuleName?.length == 0) {
          assignmentRulesErrors.value.assignmentRuleName = "Name is required";
        } else {
          assignmentRulesErrors.value.assignmentRuleName = "";
        }
        break;
      case "description":
        assignmentRulesErrors.value.description =
          assignmentRuleData.value.description?.length > 0
            ? ""
            : "Description is required";
        break;
      case "assignCondition":
        if (skipConditionCheck) {
          break;
        }
        assignmentRulesErrors.value.assignCondition =
          assignmentRuleData.value.assignConditionJson?.length > 0
            ? ""
            : "Assign condition is required";

        if (!validateConditions(assignmentRuleData.value.assignConditionJson)) {
          assignmentRulesErrors.value.assignConditionError =
            "Assign conditions are invalid";
        } else {
          assignmentRulesErrors.value.assignConditionError = "";
        }

        break;
      case "unassignCondition":
        if (skipConditionCheck) {
          break;
        }
        if (
          assignmentRuleData.value.unassignConditionJson?.length > 0 &&
          !validateConditions(assignmentRuleData.value.unassignConditionJson)
        ) {
          assignmentRulesErrors.value.unassignConditionError =
            "Unassign conditions are invalid";
        } else {
          assignmentRulesErrors.value.unassignConditionError = "";
        }
        break;
      case "users":
        assignmentRulesErrors.value.users =
          assignmentRuleData.value.users?.length > 0
            ? ""
            : "Users are required";
        break;
      case "assignmentDays":
        assignmentRulesErrors.value.assignmentDays =
          assignmentRuleData.value.assignmentDays?.length > 0
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
  assignmentRuleName: "",
  assignCondition: "",
  assignConditionError: "",
  unassignConditionError: "",
  users: "",
  description: "",
  assignmentDays: "",
});

export const resetAssignmentRuleErrors = () => {
  (Object.keys(assignmentRulesErrors.value) as string[]).forEach((key) => {
    assignmentRulesErrors.value[key] = "";
  });
};
