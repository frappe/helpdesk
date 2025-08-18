<template>
  <div class="px-10 py-8 sticky top-0">
    <div class="flex items-start justify-between">
      <div class="flex flex-col gap-1">
        <h1 class="text-lg font-semibold text-ink-gray-8">
          {{ __("Assignment rules") }}
        </h1>
        <p class="text-p-sm text-ink-gray-6 max-w-md">
          {{
            __(
              "Assignment Rules automatically route tickets to the right team members based on predefined conditions."
            )
          }}
        </p>
      </div>
      <Button
        :label="__('Create new')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="plus"
      />
    </div>
  </div>
  <div class="overflow-y-auto px-10 pb-8">
    <AssignmentRulesListView />
  </div>
</template>

<script setup lang="ts">
import { Button, createResource } from "frappe-ui";
import { provide } from "vue";
import {
  assignmentRulesActiveScreen,
  resetAssignmentRuleData,
} from "../../../stores/assignmentRules";
import AssignmentRulesListView from "./AssignmentRulesListView.vue";

const assignmentRulesListData = createResource({
  url: "helpdesk.api.assignment_rule.get_assignment_rules_list",
  cache: ["assignmentRules", "get_assignment_rules_list"],
  auto: true,
});

provide("assignmentRulesList", assignmentRulesListData);

const goToNew = () => {
  resetAssignmentRuleData();
  assignmentRulesActiveScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
