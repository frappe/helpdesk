<template>
  <SettingsLayoutBase>
    <template #title>
      <h1 class="text-lg font-semibold text-ink-gray-8">
        {{ __("Assignment Rules") }}
      </h1>
    </template>
    <template #description>
      <p class="text-p-sm max-w-md text-ink-gray-6">
        {{
          __(
            "Assignment Rules automatically route tickets to the right team members based on predefined conditions."
          )
        }}
      </p>
    </template>
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="goToNew()"
        icon-left="lucide-plus"
      />
    </template>
    <template
      v-if="
        assignmentRulesListData.data?.length > 9 ||
        assignmentRuleSearchQuery.length
      "
      #header-bottom
    >
      <div class="relative">
        <TextInput
          :model-value="assignmentRuleSearchQuery"
          @update:model-value="assignmentRuleSearchQuery = $event"
          :placeholder="__('Search')"
          type="text"
          class="focus:ring-0 border-outline-gray-2"
          :debounce="300"
        >
          <template #prefix>
            <LucideSearch class="size-4" />
          </template>
        </TextInput>
        <Button
          v-if="assignmentRuleSearchQuery"
          icon="lucide-x"
          variant="ghost"
          @click="assignmentRuleSearchQuery = ''"
          class="absolute right-1 top-1/2 -translate-y-1/2"
        />
      </div>
    </template>
    <template #content>
      <AssignmentRulesListView />
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { Button, createResource } from "frappe-ui";
import { inject, provide, Ref } from "vue";
import {
  assignmentRulesActiveScreen,
  resetAssignmentRuleData,
} from "@/stores/assignmentRules";
import AssignmentRulesListView from "./AssignmentRulesListView.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { AssignmentRuleListResourceSymbol } from "@/types";

const assignmentRulesListData = createResource({
  url: "helpdesk.api.assignment_rule.get_assignment_rules_list",
  cache: ["assignmentRules", "get_assignment_rules_list"],
  auto: true,
});
const assignmentRuleSearchQuery = inject<Ref>("assignmentRuleSearchQuery");

provide(AssignmentRuleListResourceSymbol, assignmentRulesListData);

const goToNew = () => {
  resetAssignmentRuleData();
  assignmentRulesActiveScreen.value = {
    screen: "view",
    data: null,
  };
};
</script>
