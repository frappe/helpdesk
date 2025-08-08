<template>
  <div>
    <div class="flex flex-col gap-2">
      <span class="text-lg font-semibold text-ink-gray-7">Assignee Rules</span>
      <span class="text-sm text-ink-gray-6">
        Define who receives the tickets and how they’re distributed among
        agents.
      </span>
    </div>
    <div class="mt-10 flex items-center justify-between gap-2">
      <div>
        <div class="text-base font-medium text-ink-gray-7">Ticket Routing</div>
        <div class="text-sm text-ink-gray-6 mt-2">
          Choose how tickets are distributed among selected assignees.
        </div>
      </div>
      <div>
        <Popover placement="bottom-end">
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 pl-2 pr-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] select-none min-w-40"
              @click="togglePopover()"
            >
              <div>
                {{
                  ticketRoutingOptions.find(
                    (option) => option.value == assignmentRuleData.rule
                  )?.label
                }}
              </div>
              <FeatherIcon name="chevron-down" class="size-4" />
            </div>
          </template>
          <template #body="{ togglePopover }">
            <div
              class="p-1 text-ink-gray-7 mt-1 w-48 bg-white shadow-xl rounded"
            >
              <div
                v-for="option in ticketRoutingOptions"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-gray-50 text-sm flex items-center justify-between rounded"
                @click="
                  () => {
                    assignmentRuleData.rule = option.value;
                    togglePopover();
                  }
                "
              >
                <span>
                  {{ option.label }}
                </span>
                <FeatherIcon
                  v-if="assignmentRuleData.rule == option.value"
                  name="check"
                  class="size-4"
                />
              </div>
            </div>
          </template>
        </Popover>
      </div>
    </div>
    <div class="mt-10 flex items-center justify-between gap-2">
      <div>
        <div class="text-base font-medium text-ink-gray-7">Assignees</div>
        <div class="text-sm text-ink-gray-6 mt-2">
          Choose who receives the tickets.
        </div>
      </div>
      <AssigneeSearch @addAssignee="validateAssignmentRule('users')" />
    </div>
    <div class="mt-4 flex flex-wrap gap-2">
      <div
        v-for="user in assignmentRuleData.users"
        :key="user.name"
        class="flex items-center gap-2 text-sm bg-surface-gray-2 rounded-md p-1 w-max px-2 select-none"
      >
        <Avatar :image="user.user_image" :label="user.user" size="sm" />
        <div class="text-ink-gray-7">
          {{ user.user }}
        </div>
        <Tooltip
          v-if="user.user == assignmentRuleData.last_user"
          text="Last user assigned by this rule"
          :hover-delay="0.35"
          :placement="'top'"
        >
          <div
            class="text-xs rounded-full select-none bg-blue-600 text-white p-0.5 px-2"
          >
            Last
          </div>
        </Tooltip>
        <Button variant="ghost" icon="x" @click="removeAssignedUser(user)" />
      </div>
    </div>
    <ErrorMessage :message="assignmentRulesErrors.users" />
  </div>
</template>

<script setup lang="ts">
import { Avatar, Button, ErrorMessage, Popover, Tooltip } from "frappe-ui";
import {
  assignmentRuleData,
  assignmentRulesErrors,
  validateAssignmentRule,
} from "../../../stores/assignmentRules";
import AssigneeSearch from "./AssigneeSearch.vue";

const ticketRoutingOptions = [
  {
    label: "Auto-rotate",
    value: "Round Robin",
  },
  {
    label: "Assign by workload",
    value: "Load Balancing",
  },
];

const removeAssignedUser = (user) => {
  assignmentRuleData.value.users = assignmentRuleData.value.users.filter(
    (u) => u.user !== user.user
  );
  validateAssignmentRule("users");
};
</script>
