<template>
  <SettingsHeader :routes="routes" />
  <div
    class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
  >
    <div>
      <div
        v-if="assignmentRulesList.loading && !assignmentRulesList.data"
        class="flex items-center justify-center mt-12"
      >
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else>
        <div
          v-if="
            !assignmentRulesList.loading && !assignmentRulesList.data?.length
          "
          class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
        >
          <div class="p-4 size-16 rounded-full bg-surface-gray-1">
            <Settings class="size-8 text-ink-gray-6 rotate-90" />
          </div>
          <div class="flex flex-col items-center gap-1">
            <div class="text-lg font-medium text-ink-gray-6">
              No assignment rule found
            </div>
            <div class="text-base text-ink-gray-5 max-w-60 text-center">
              Add your first assignment rule to get started.
            </div>
          </div>
          <Button
            label="New"
            variant="outline"
            icon-left="plus"
            @click="goToNew()"
          />
        </div>
        <div v-else>
          <div
            class="grid grid-cols-8 sm:grid-cols-11 items-center gap-4 text-p-sm text-gray-600"
          >
            <div class="col-span-3 sm:col-span-7">
              {{ __("Assignment rule") }}
            </div>
            <div class="col-span-3 sm:col-span-2">{{ __("Priority") }}</div>
            <div class="col-span-2">{{ __("Enabled") }}</div>
          </div>
          <hr class="mt-2" />
          <div
            v-for="assignmentRule in assignmentRulesList.data"
            :key="assignmentRule.name"
          >
            <AssignmentRuleListItem :data="assignmentRule" />
            <hr />
          </div>
        </div>
      </div>
    </div>
    <div
      v-if="assignmentRulesList.data?.length"
      class="bg-white py-4 lg:py-8 lg:pb-6 sticky top-0"
    >
      <SettingsLayoutHeader
        :title="__('Assignment rules')"
        :description="
          __(
            'Assignment Rules automatically route tickets to the right team members based on predefined conditions'
          )
        "
      >
        <template #actions>
          <Button
            :label="__('New')"
            theme="gray"
            variant="solid"
            @click="goToNew()"
            icon-left="plus"
          />
        </template>
      </SettingsLayoutHeader>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, provide } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { resetAssignmentRuleData } from "@/stores/assignmentRules";
import { Button, createResource, LoadingIndicator } from "frappe-ui";
import AssignmentRuleListItem from "./components/AssignmentRuleListItem.vue";
import { useRouter } from "vue-router";
import SettingsLayoutHeader from "../components/SettingsLayoutHeader.vue";
import Settings from "~icons/lucide/settings-2";

const router = useRouter();

const assignmentRulesList = createResource({
  url: "helpdesk.api.assignment_rule.get_assignment_rules_list",
  cache: ["assignmentRules", "get_assignment_rules_list"],
  auto: true,
});

provide("assignmentRulesList", assignmentRulesList);

const routes = computed(() => [
  {
    label: "Assignment Rules",
    route: "/settings/assignment-rules",
  },
]);

const goToNew = () => {
  resetAssignmentRuleData();
  router.push({
    name: "NewAssignmentRule",
  });
};
</script>
