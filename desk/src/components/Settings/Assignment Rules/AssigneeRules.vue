<template>
  <div>
    <div class="flex flex-col gap-1">
      <span class="text-lg-semibold text-ink-gray-8">{{
        __("Assignee Rules")
      }}</span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __(
            "Define who receives the tickets and how they’re distributed among agents."
          )
        }}
      </span>
    </div>
    <div class="mt-8 flex items-center justify-between gap-2">
      <div>
        <div class="text-base-medium text-ink-gray-8">
          {{ __("Ticket Routing") }}
        </div>
        <div class="text-p-sm text-ink-gray-6 mt-1">
          {{
            __("Choose how tickets are distributed among selected assignees.")
          }}
        </div>
      </div>
      <div>
        <Popover placement="bottom-end">
          <template #target="{ togglePopover }">
            <div
              class="flex items-center justify-between text-base rounded h-7 py-1.5 ps-2 pe-2 border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-elevation-2 hover:bg-surface-gray-3 focus:bg-surface-base focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors w-full dark:[color-scheme:dark] select-none min-w-44"
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
              class="p-1 text-ink-gray-7 mt-1 bg-surface-base shadow-xl rounded w-[--reka-popper-anchor-width]"
            >
              <div
                v-for="option in ticketRoutingOptions"
                :key="option.value"
                class="p-2 cursor-pointer hover:bg-surface-gray-3 text-sm flex items-center justify-between rounded"
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
    <div class="mt-7 flex items-center justify-between gap-2">
      <div>
        <div class="text-base-medium text-ink-gray-8">
          {{ __("Assignees") }}
        </div>
        <div class="text-p-sm text-ink-gray-6 mt-1">
          {{ __("Choose who receives the tickets.") }}
        </div>
      </div>
      <AssigneeSearch @addAssignee="validateAssignmentRule('users')" />
    </div>
    <div class="mt-4 flex flex-wrap gap-2">
      <Button
        v-for="user in users"
        :key="user.name"
        variant="outline"
        size="sm"
        :label="user.full_name"
      >
        <template #prefix>
          <Avatar :image="user.user_image" :label="user.full_name" size="sm" />
        </template>
        <template #suffix>
          <Tooltip
            v-if="user.email == assignmentRuleData.lastUser"
            :text="__('Last user assigned by this rule')"
            :hover-delay="0.35"
            placement="top"
          >
            <Badge theme="blue" variant="solid" :label="__('Last')" />
          </Tooltip>
          <LucideX
            class="size-4 text-ink-gray-4 transition-colors hover:text-ink-gray-7"
            @click.stop="removeAssignedUser(user)"
          />
        </template>
      </Button>
    </div>
    <ErrorMessage :message="assignmentRulesErrors.users" />
  </div>
</template>

<script setup lang="ts">
import {
  assignmentRuleData,
  assignmentRulesErrors,
  validateAssignmentRule,
} from "@/stores/assignmentRules";
import { useUserStore } from "@/stores/user";
import {
  Avatar,
  Badge,
  Button,
  ErrorMessage,
  Popover,
  Tooltip,
} from "frappe-ui";
import LucideX from "~icons/lucide/x";
import { computed } from "vue";
import AssigneeSearch from "./AssigneeSearch.vue";

const { getUser } = useUserStore();

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
    (u) => u.user !== user.name
  );
  validateAssignmentRule("users");
};

const users = computed(() => {
  const _users = [];
  assignmentRuleData.value.users.forEach((user) => {
    _users.push(getUser(user.user));
  });
  return _users;
});
</script>
