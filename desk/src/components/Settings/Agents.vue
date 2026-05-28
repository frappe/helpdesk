<template>
  <SettingsLayoutBase
    :title="__('Agents')"
    :description="__('Add, manage agents and assign roles to them.')"
  >
    <template #header-actions>
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
    <template #header-bottom>
      <div class="flex items-center gap-2 justify-between">
        <div class="relative grow">
          <TextInput
            :model-value="search"
            @update:model-value="search = $event"
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
            v-if="search"
            icon="lucide-x"
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
          <template #item-label="{ item }">
            <button
              class="group flex text-ink-gray-6 gap-4 w-full justify-between items-center rounded text-base"
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
    <template #content>
      <div class="grow">
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
        <EmptyState
          v-if="!agents.loading && !agents.data?.length"
          variant="badge"
          :icon="AgentIcon"
          title="No agent found"
          :description="
            activeFilter.length
              ? 'Change your search terms or filters'
              : 'Add one to get started.'
          "
        />
        <!-- Agent List -->
        <div
          class="w-full"
          v-if="!agents.loading && Boolean(agents.data?.length)"
        >
          <div
            class="grid grid-cols-8 items-center gap-3 text-sm text-ink-gray-5"
          >
            <div class="col-span-6 text-p-sm">{{ __("Agent name") }}</div>
          </div>
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
          <hr class="mt-2" />
          <div v-for="(agent, index) in agents.data" :key="agent.agent_name">
            <div class="flex items-center justify-between h-14 group rounded">
              <div class="flex items-center space-x-3 grow">
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
              <div class="flex items-center gap-2">
                <Dropdown
                  v-if="isManager"
                  class="flex justify-end items-center"
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
<<<<<<< HEAD
                  <Button icon="lucide-more-horizontal" variant="ghost" />
=======
                  <Button icon="more-horizontal" variant="ghost" />
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
                </Dropdown>
              </div>
            </div>
            <hr v-if="index !== agents.data.length - 1" />
<<<<<<< HEAD
=======
          <hr class="mt-2 mx-2" />
          <div v-for="(agent, index) in agents.data" :key="agent.name">
            <AgentRow
              :agent="agent"
              :stats="statsFor(agent.name)"
              :is-manager="isManager"
              :current-role="getUserRole(agent.name)"
              :kebab-options="kebabOptionsFor(agent)"
              @update:role="(role) => updateRole(agent.name, role)"
            />
            <hr v-if="index !== agents.data.length - 1" class="mx-2" />
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)
=======
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
          </div>
          <!-- Load More Button -->
          <div class="flex justify-center">
            <Button
              v-if="!agents.loading && agents.hasNextPage"
              class="mt-3.5 p-2"
              @click="() => agents.next()"
              :loading="agents.loading"
              :label="__('Load More')"
              icon-left="lucide-refresh-cw"
            />
          </div>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
<<<<<<< HEAD
import { __ } from "@/translation";
<<<<<<< HEAD
import { renderOptionIcon } from "@/utils";
=======
import { Button, Dropdown, FeatherIcon, call, toast } from "frappe-ui";
import { computed, onUnmounted } from "vue";
import AgentIcon from "../icons/AgentIcon.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import AgentRow from "./AgentRow.vue";
=======
import { Avatar, Button, call, Dropdown, FeatherIcon, toast } from "frappe-ui";
import { h, onUnmounted } from "vue";
import LucideCheck from "~icons/lucide/check";
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
import { activeFilter, useAgents } from "./agents";
import AgentIcon from "../icons/AgentIcon.vue";
import { setActiveSettingsTab } from "./settingsModal";
<<<<<<< HEAD
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)
=======
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")

const { getUserRole, updateUserRoleCache } = useUserStore();
const { isManager } = useAuthStore();

const agentStore = useAgents();
const search = agentStore.search;
const agents = agentStore.agents;

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
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
<<<<<<< HEAD
          icon: "lucide-user",
=======
          icon: "user",
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
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
<<<<<<< HEAD
          icon: "lucide-briefcase",
=======
          icon: "briefcase",
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
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

        "group flex w-full text-ink-gray-8 justify-between items-center rounded-md px-2 py-2 text-sm hover:bg-surface-gray-3",
      ],
      onClick: !selected ? onClick : null,
    },
    [
      h("div", { class: "flex gap-2" }, [
<<<<<<< HEAD
        renderOptionIcon(icon),
=======
        icon
          ? h(FeatherIcon, {
              name: icon,
              class: ["h-4 w-4 shrink-0"],
              "aria-hidden": true,
            })
          : null,
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
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
<<<<<<< HEAD
=======
const { statsFor } = useAgentWorkload(computed(() => agents.data));
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)
=======
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")

  call("helpdesk.helpdesk.doctype.hd_agent.hd_agent.update_agent_role", {
    user: agent,
    new_role: newRole,
  }).then(() => {
    updateUserRoleCache(agent, newRole);
    toast.success(__(`Role updated to ${newRole} successfully.`));
  });
}

function getOptions(agent) {
  let filters = agentStore.filters;
  return [
    {
      label: "Disable Agent",
<<<<<<< HEAD
      icon: "lucide-x-circle",
      onClick: async () => {
        await agentStore.updateAgent(agent.name, 0);
        agents.reload({ ...filters, search: search.value });
      },
      condition: () => agent.is_active,
    },
    {
      label: "Enable Agent",
      icon: "lucide-check-circle",
      onClick: async () => {
        await agentStore.updateAgent(agent.name, 1);
        agents.reload({ ...filters, search: search.value });
      },
=======
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
<<<<<<< HEAD
      onClick: () => setAgentActive(agent.name, 1),
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)
=======
      onClick: async () => {
        await agentStore.updateAgent(agent.name, 1);
        agents.reload({ ...filters, search: search.value });
      },
>>>>>>> 065026b2 (Revert "feat: add open tickets and avg first response in agents tab")
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
