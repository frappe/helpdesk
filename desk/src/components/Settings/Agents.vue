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
        <Dropdown :options="activeFilterOptions" placement="right">
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
              class="group flex text-ink-gray-6 gap-4 w-full justify-between items-center rounded text-p-sm"
              @click="item.onClick"
            >
              <span class="whitespace-nowrap">{{ item.label }}</span>
              <FeatherIcon
                v-if="activeFilter === item.label"
                name="check"
                class="size-4 text-ink-gray-7"
              />
            </button>
          </template>
        </Dropdown>
      </div>
    </template>
    <template #content>
      <div class="grow">
        <div
          v-if="agents.loading"
          class="flex mt-28 justify-between w-full h-full"
        >
          <Button :loading="true" variant="ghost" class="w-full" size="2xl" />
        </div>
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
        <div
          v-if="!agents.loading && Boolean(agents.data?.length)"
          class="-ml-2 w-full"
        >
          <div
            class="grid grid-cols-12 items-center gap-4 text-xs tracking-wider text-ink-gray-5"
          >
            <div class="col-span-4 ml-2">{{ __("Agent") }}</div>
            <div class="col-span-3">{{ __("Tickets") }}</div>
            <div class="col-span-2 -ml-4">{{ __("First Response") }}</div>
            <div v-if="isManager" class="col-span-2">{{ __("Role") }}</div>
            <div :class="isManager ? 'col-span-1' : 'col-span-3'" />
          </div>
<<<<<<< HEAD
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
                  <Button icon="lucide-more-horizontal" variant="ghost" />
                </Dropdown>
              </div>
            </div>
            <hr v-if="index !== agents.data.length - 1" />
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
          </div>
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
import { useAgentWorkload } from "@/composables/useAgentWorkload";
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { __ } from "@/translation";
<<<<<<< HEAD
import { renderOptionIcon } from "@/utils";
=======
import { Button, Dropdown, FeatherIcon, call, toast } from "frappe-ui";
import { computed, onUnmounted } from "vue";
import AgentIcon from "../icons/AgentIcon.vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import AgentRow from "./AgentRow.vue";
import { activeFilter, useAgents } from "./agents";
import { setActiveSettingsTab } from "./settingsModal";
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)

const { getUserRole, updateUserRoleCache } = useUserStore();
const { isManager } = useAuthStore();
const agentStore = useAgents();
const search = agentStore.search;
const agents = agentStore.agents;

<<<<<<< HEAD
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
          icon: "lucide-user",
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
          icon: "lucide-briefcase",
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
        renderOptionIcon(icon),
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
=======
const { statsFor } = useAgentWorkload(computed(() => agents.data));
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)

function updateRole(agentName: string, newRole: string) {
  if (getUserRole(agentName) === newRole) return;
  call("helpdesk.helpdesk.doctype.hd_agent.hd_agent.update_agent_role", {
    user: agentName,
    new_role: newRole,
  }).then(() => {
    updateUserRoleCache(agentName, newRole);
    toast.success(__(`Role updated to ${newRole} successfully.`));
  });
}

function kebabOptionsFor(agent: { name: string; is_active: boolean | number }) {
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
      onClick: () => setAgentActive(agent.name, 0),
      condition: () => Boolean(agent.is_active),
    },
    {
      label: "Enable Agent",
      icon: "check-circle",
      onClick: () => setAgentActive(agent.name, 1),
>>>>>>> 85edb100 (feat: add open tickets and avg first response in agents tab)
      condition: () => !agent.is_active,
    },
  ];
}

async function setAgentActive(agentName: string, isActive: 0 | 1) {
  await agentStore.updateAgent(agentName, isActive);
  agents.reload({ ...agentStore.filters, search: search.value });
}

const activeFilterOptions = [
  {
    label: "All",
    onClick: () => setActiveFilter("All", ["in", [0, 1]]),
  },
  { label: "Active", onClick: () => setActiveFilter("Active", ["=", 1]) },
  { label: "Inactive", onClick: () => setActiveFilter("Inactive", ["=", 0]) },
];

function setActiveFilter(label: string, isActiveFilter: unknown) {
  agentStore.filters["is_active"] = isActiveFilter;
  activeFilter.value = label;
}

onUnmounted(() => {
  agents.filters = {};
});
</script>
