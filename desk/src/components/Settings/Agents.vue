<template>
  <div v-bind:class="$attrs.class">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-lg font-semibold">{{ __("Agents") }}</h1>
      <div class="flex item-center space-x-2">
        <FormControl
          v-model="search"
          :placeholder="'Search'"
          type="text"
          :debounce="300"
        >
          <template #prefix>
            <LucideSearch class="h-4 w-4 text-gray-500" />
          </template>
        </FormControl>
        <Dropdown :options="dropdownOptions" placement="right">
          <template #default="{ open }">
            <Button
              :label="activeFilter"
              class="flex items-center justify-between w-[90px]"
            >
              <template #suffix>
                <FeatherIcon
                  :name="open ? 'chevron-up' : 'chevron-down'"
                  class="h-4"
                />
              </template>
            </Button>
          </template>
          <template #item="{ item, active }">
            <button
              class="group flex text-ink-gray-6 gap-4 h-7 w-full justify-between items-center rounded px-2 text-base"
              :class="{ 'bg-surface-gray-3': active }"
              @click="item.onClick"
            >
              <div class="flex items-center justify-between flex-1">
                <span class="whitespace-nowrap">
                  {{ item.label }}
                </span>
                <FeatherIcon
                  v-if="activeFilter === item.label"
                  name="check"
                  class="size-4 text-ink-gray-7"
                />
              </div>
            </button>
          </template>
        </Dropdown>
        <Button
          @click="() => (showNewAgentsDialog = !showNewAgentsDialog)"
          label="New"
          variant="solid"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4 stroke-1.5" />
          </template>
        </Button>
      </div>
    </div>

    <!-- loading state -->
    <div v-if="agents.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="agents.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>
    <!-- Empty State -->
    <div
      v-if="!agents.loading && !agents.data?.length"
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        No agents found
      </p>
    </div>
    <!-- Agent List -->
    <div
      class="overflow-y-auto w-full hide-scrollbar"
      v-if="!agents.loading && Boolean(agents.data?.length)"
    >
      <div v-for="(agent, idx) in agents.data" :key="agent.agent_name">
        <AgentCard
          :agent="agent"
          :show-status="true"
          :class="idx !== agents.data.length - 1 && 'border-b '"
        >
          <template #right>
            <Dropdown
              v-if="isManager"
              class="w-1/5 flex justify-end items-center"
              :options="getRoles(agent.name)"
              :label="getUserRole(agent.name)"
              :button="{
                label: getUserRole(agent.name),
                iconRight: 'chevron-down',
              }"
              placement="right"
            />
            <Dropdown
              :options="getOptions(agent)"
              placement="right"
              :key="agent"
              class="ml-2"
            >
              <Button>
                <template #icon>
                  <IconMoreHorizontal class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
          </template>
        </AgentCard>
      </div>
      <!-- Load More Button -->
      <div class="flex justify-center">
        <Button
          v-if="!agents.loading && agents.hasNextPage"
          class="mt-3.5 p-2"
          @click="() => agents.next()"
          :loading="agents.loading"
          label="Load More"
          icon-left="refresh-cw"
        />
      </div>
    </div>
  </div>
  <AddNewAgentsDialog
    @close="showNewAgentsDialog = false"
    :modelValue="showNewAgentsDialog"
    :show="showNewAgentsDialog"
    @update:modelValue="showNewAgentsDialog = $event"
  />
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { call, FormControl, toast } from "frappe-ui";
import { h } from "vue";
import LucideCheck from "~icons/lucide/check";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import AgentCard from "./AgentCard.vue";
import { activeFilter, showNewAgentsDialog, useAgents } from "./agents";

const { getUserRole, updateUserRoleCache } = useUserStore();
const { isManager } = useAuthStore();

const agentStore = useAgents();
const search = agentStore.search;
const agents = agentStore.agents;

function getRoles(agent: string) {
  const agentRole = getUserRole(agent);
  const roles = [
    {
      label: "Agent",
      component: (props) =>
        RoleOption({
          role: "Agent",
          active: props.active,
          selected: agentRole === "Agent",
          onClick: () => {
            updateRole(agent, "Agent");
          },
        }),
    },
  ];
  if (isManager) {
    roles.unshift({
      label: "Manager",
      component: (props) =>
        RoleOption({
          role: "Manager",
          active: props.active,
          selected: agentRole === "Manager",
          onClick: () => {
            updateRole(agent, "Manager");
          },
        }),
    });
  }

  return roles;
}
function RoleOption({ active, role, onClick, selected }) {
  return h(
    "button",
    {
      class: [
        active ? "bg-surface-gray-2" : "text-ink-gray-7",
        "group flex w-full justify-between items-center rounded-md px-2 py-2 text-base",
      ],
      onClick: !selected ? onClick : null,
    },
    [
      h("span", { class: "whitespace-nowrap" }, role),
      selected
        ? h(LucideCheck, {
            class: ["h-4 w-4 shrink-0 text-ink-gray-7"],
            "aria-hidden": true,
          })
        : null,
    ]
  );
}
function updateRole(agent: string, newRole: string) {
  const currentRole = getUserRole(agent);
  if (currentRole === newRole) {
    return;
  }

  call("helpdesk.helpdesk.doctype.hd_agent.hd_agent.update_agent_role", {
    user: agent,
    new_role: newRole,
  }).then(() => {
    updateUserRoleCache(agent, newRole);
    toast.success(`Role updated to ${newRole}`);
  });
}

function getOptions(agent) {
  let filters = agentStore.filters;
  return [
    {
      label: "Disable Agent",
      icon: "x-circle",
      onClick: async () => {
        await agentStore.updateAgent(agent.name, 0);
        agents.reload({ ...filters, search: search.value });
      },
      condition: () => agent.is_active,
    },
    {
      label: "Enable Agent",
      icon: "check-circle",
      onClick: async () => {
        await agentStore.updateAgent(agent.name, 1);
        agents.reload({ ...filters, search: search.value });
      },
      condition: () => !agent.is_active,
    },
  ];
}

const dropdownOptions = [
  {
    label: "All",
    onClick: () => {
      agentStore.filters["is_active"] = ["in", [0, 1]];
      activeFilter.value = "All";
    },
  },
  {
    label: "Active",
    onClick: () => {
      agentStore.filters["is_active"] = ["=", 1];
      activeFilter.value = "Active";
    },
  },
  {
    label: "Inactive",
    onClick: () => {
      agentStore.filters["is_active"] = ["=", 0];
      activeFilter.value = "Inactive";
    },
  },
];
</script>

<style scoped></style>
