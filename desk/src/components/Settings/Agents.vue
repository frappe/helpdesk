<template>
  <div v-bind:class="$attrs.class" class="pb-6">
    <!-- Header -->
    <div class="px-10 py-8">
      <SettingsLayoutHeader
        :title="__('Agents')"
        :description="__('Add, manage agents and assign roles to them.')"
      >
        <template #actions>
          <Button
            @click="() => setActiveSettingsTab('Invite Agents')"
            label="New"
            variant="solid"
          >
            <template #prefix>
              <LucidePlus class="h-4 w-4 stroke-1.5" />
            </template>
          </Button>
        </template>
        <template
          #bottom-section
          v-if="!agents.loading && Boolean(agents.data?.length)"
        >
          <div class="flex items-center gap-2 justify-between">
            <div class="relative grow">
              <Input
                v-model="search"
                @input="search = $event"
                :placeholder="__('Search')"
                type="text"
                class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
                icon-left="search"
                debounce="300"
                inputClass="p-4 pr-12"
              />
              <Button
                v-if="search"
                icon="x"
                variant="ghost"
                @click="search = ''"
                class="absolute right-1 top-1/2 -translate-y-1/2"
              />
            </div>
            <Dropdown :options="dropdownOptions" placement="right">
              <template #default="{ open }">
                <Button
                  :label="activeFilter"
                  class="flex items-center justify-between w-fit p-4"
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
          </div>
        </template>
      </SettingsLayoutHeader>
    </div>
    <div class="px-10 pb-8 overflow-y-auto">
      <!-- loading state -->
      <div
        v-if="agents.loading"
        class="flex mt-28 justify-between w-full h-full"
      >
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
        class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
      >
        <div
          class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex items-center justify-center"
        >
          <AgentIcon class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No agent found") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{
              activeFilter.length
                ? __("Change your search terms or filters")
                : __("Add your first agent to get started.")
            }}
          </div>
        </div>
        <Button
          :label="__('Add Agent')"
          variant="outline"
          icon-left="plus"
          @click="setActiveSettingsTab('Invite Agents')"
        />
      </div>
      <!-- Agent List -->
      <div
        class="w-full"
        v-if="!agents.loading && Boolean(agents.data?.length)"
      >
        <div class="grid grid-cols-8 items-center gap-3 text-sm text-gray-600">
          <div class="col-span-6 text-p-sm">{{ __("Agent Name") }}</div>
        </div>
        <hr class="mt-2" />
        <div v-for="agent in agents.data" :key="agent.agent_name">
          <div class="flex items-center justify-between h-14 group rounded">
            <div class="flex items-center space-x-3 w-4/5">
              <Avatar
                :image="agent.user_image"
                :label="agent.agent_name"
                size="xl"
              />
              <div>
                <div class="flex items-center gap-2">
                  <p class="text-base">
                    {{ agent.agent_name }}
                  </p>
                  <Badge
                    :label="__('Inactive')"
                    :theme="'gray'"
                    :class="!agent.is_active ? 'opacity-100' : 'opacity-0'"
                    variant="subtle"
                  />
                </div>
                <div class="text-base text-ink-gray-6 mt-1">
                  {{ agent.name }}
                </div>
              </div>
            </div>
            <Dropdown
              v-if="isManager"
              class="w-1/5 flex justify-end items-center"
              :options="getRoles(agent.name)"
              :label="getUserRole(agent.name)"
              :button="{
                label: getUserRole(agent.name),
                iconRight: 'chevron-down',
                iconLeft:
                  getUserRole(agent.name) === 'Agent'
                    ? 'user'
                    : getUserRole(agent.name) === 'Manager'
                    ? 'briefcase'
                    : null,
              }"
              placement="right"
            />
            <Dropdown
              :options="getOptions(agent)"
              :key="agent"
              class="ml-2"
              placement="right"
            >
              <Button icon="more-horizontal" variant="ghost" />
            </Dropdown>
          </div>
          <hr />
        </div>
        <!-- Load More Button -->
        <div class="flex justify-center">
          <Button
            v-if="!agents.loading && agents.hasNextPage"
            class="mt-3.5 p-2"
            @click="() => agents.next()"
            :loading="agents.loading"
            :label="__('Load More')"
            icon-left="refresh-cw"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { Avatar, Button, call, FeatherIcon, toast } from "frappe-ui";
import { h, onUnmounted } from "vue";
import LucideCheck from "~icons/lucide/check";
import { activeFilter, useAgents } from "./agents";
import AgentIcon from "../icons/AgentIcon.vue";
import { setActiveSettingsTab } from "./settingsModal";

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
          icon: "user",
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
          icon: "briefcase",
          onClick: () => {
            updateRole(agent, "Manager");
          },
        }),
    });
  }

  return roles;
}

function RoleOption({ active, role, onClick, selected, icon = null }) {
  return h(
    "button",
    {
      class: [
        active ? "bg-surface-gray-2" : "text-ink-gray-7",

        "group flex w-full text-ink-gray-8 justify-between items-center rounded-md px-2 py-2 text-sm hover:bg-surface-gray-2",
      ],
      onClick: !selected ? onClick : null,
    },
    [
      h("div", { class: "flex gap-2" }, [
        icon
          ? h(FeatherIcon, {
              name: icon,
              class: ["h-4 w-4 shrink-0"],
              "aria-hidden": true,
            })
          : null,
        h("span", { class: "whitespace-nowrap" }, role),
      ]),
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

onUnmounted(() => {
  agents.filters = {};
});
</script>
