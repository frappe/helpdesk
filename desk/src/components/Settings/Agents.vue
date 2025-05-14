<template>
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <h1 class="text-lg font-semibold">Agents</h1>
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
      <Button @click="() => (showForm = !showForm)" label="New ">
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
  <div class="divide-y" v-if="!agents.loading && Boolean(agents.data?.length)">
    <div v-for="agent in agents.data">
      <div class="flex items-center justify-between py-3">
        <div class="flex items-center space-x-3 w-4/5">
          <Avatar
            :image="agent.user_image"
            :label="agent.agent_name"
            size="lg"
          />
          <div>
            <div class="text-base font-semibold text-ink-gray-8">
              {{ agent.agent_name }}
            </div>
            <div class="text-base text-ink-gray-6 mt-1">
              {{ agent.name }}
            </div>
          </div>
        </div>
        <p v-if="!isManager" class="text-sm text-ink-gray-6 w-1/5 text-left">
          {{ getUserRole(agent.name) }}
        </p>

        <Dropdown
          v-if="isManager"
          class="w-1/5"
          :options="getRoles(agent.name)"
          :label="getUserRole(agent.name)"
          :button="{
            label: getUserRole(agent.name),
            iconRight: 'chevron-down',
            variant: 'ghost',
          }"
          placement="right"
        />
      </div>
    </div>
  </div>
  <!-- Load More Button -->
  <div class="flex justify-center">
    <Button
      v-if="!agents.loading && agents.hasNextPage"
      class="my-5 p-2"
      @click="() => agents.next()"
      :loading="agents.loading"
      label="Load More"
      icon-left="refresh-cw"
    />
  </div>
  <AddNewAgentsDialog
    :show="showForm"
    @close="showForm = false"
    :modelValue="showForm"
  />
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useUserStore } from "@/stores/user";
import { createToast } from "@/utils";
import { Avatar, call, createListResource, FormControl } from "frappe-ui";
import { h, ref, watch } from "vue";
import LucideCheck from "~icons/lucide/check";

const { getUserRole, updateUserRoleCache } = useUserStore();
const { isManager } = useAuthStore();
const showForm = ref(false);

const agents = createListResource({
  doctype: "HD Agent",
  fields: ["name", "user_image", "agent_name"],
  filters: {
    is_active: ["=", 1],
  },
  start: 0,
  pageLength: 10,
  orderBy: "creation desc",
  auto: true,
});

const search = ref("");
watch(search, (newValue) => {
  agents.filters = {
    is_active: ["=", 1],
    agent_name: ["like", `%${newValue}%`],
  };
  agents.reload();
});

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
        active ? "bg-surface-gray-2" : "text-ink-gray-9",
        "group flex w-full justify-between items-center rounded-md px-2 py-2 text-sm",
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
    createToast({
      title: "Role Updated Successfully",
      text: `${agent} role updated to ${newRole}`,
      icon: "check",
      iconClasses: "text-ink-green-3",
    });
  });
}
</script>

<style scoped></style>
