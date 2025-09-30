<template>
  <SettingsHeader :routes="routes" />
  <div
    class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
  >
    <!-- Add member -->
    <div class="flex flex-col gap-6 h-full">
      <div class="flex gap-2 items-center">
        <!-- Form control for search -->
        <div class="flex flex-col gap-1.5 w-full">
          <div class="flex gap-2">
            <div class="group border rounded flex flex-1">
              <EmailMultiSelect
                class="flex-1"
                :placeholder="__('john@doe.com')"
                inputClass="!bg-white"
                v-model="invitees"
                :validate="validateEmail"
                :error-message="
                  (value) => __('{0} is an invalid email address', [value])
                "
                :emptyPlaceholder="__('Type an email address to invite')"
                :fetchUsers="true"
                :existingEmails="teamMembers.map((m) => m.name)"
                variant="subtle"
              />
            </div>
            <Button
              label="Add Member"
              variant="solid"
              :disabled="!invitees.length"
              @click="addMember(invitees)"
            >
              <template #prefix>
                <LucidePlus class="h-4 w-4 stroke-1.5" />
              </template>
            </Button>
          </div>
        </div>
      </div>

      <!-- Member List -->
      <div class="w-full" v-if="teamMembers?.length > 0">
        <div class="grid grid-cols-8 items-center gap-3 text-sm text-gray-600">
          <div class="col-span-6 text-p-sm">
            Members ({{ teamMembers.length }})
          </div>
        </div>
        <hr class="mt-2" />
        <div v-for="member in teamMembers" :key="member.name">
          <div class="grid grid-cols-8 items-center gap-4 group">
            <div class="w-full p-2 col-span-8">
              <AgentCard :agent="member" class="!py-0">
                <template #right>
                  <Dropdown :options="memberDropdownOptions(member)">
                    <Button
                      icon="more-horizontal"
                      variant="ghost"
                      @click="isConfirmingDelete = false"
                    />
                  </Dropdown>
                </template>
              </AgentCard>
            </div>
          </div>
          <hr />
        </div>
      </div>
      <div
        v-else
        class="flex flex-col items-center justify-center h-[350px] gap-4"
      >
        <div class="p-4 size-16 rounded-full bg-surface-gray-1">
          <AgentIcon class="size-8 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-lg font-medium text-ink-gray-6">
            No members found
          </div>
          <div class="text-base text-ink-gray-5 max-w-60 text-center">
            Add your first member to get started.
          </div>
        </div>
      </div>
    </div>

    <!-- Header -->
    <div
      class="flex items-center justify-between bg-white py-4 lg:py-8 lg:pb-6 sticky top-0"
    >
      <div class="flex items-center gap-1 justify-center -ml-[16px]">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="_teamName"
          size="md"
          class="cursor-pointer hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-xl hover:opacity-70 !pr-0 max-w-48 md:max-w-60 lg:max-w-max overflow-ellipsis overflow-hidden"
          @click="router.push({ name: 'SettingsTeams' })"
        />
      </div>
      <Dropdown :options="options">
        <Button variant="ghost">
          <template #icon>
            <LucideMoreHorizontal class="h-4 w-4" />
          </template>
        </Button>
      </Dropdown>
    </div>
    <Dialog v-model="showDelete" :options="{ title: 'Delete team' }">
      <template #body-content>
        <p class="text-p-base text-ink-gray-7">
          Are you sure you want to delete this team? This action cannot be
          reversed!
        </p>
        <Button
          variant="solid"
          class="mt-4 float-right"
          label="Confirm"
          theme="red"
          @click="
            () => {
              team.delete.submit();
              showDelete = false;
            }
          "
        />
      </template>
    </Dialog>
    <RenameTeamModal v-model="showRename" @onRename="onRename" />
  </div>
</template>

<script setup lang="ts">
import SettingsHeader from "../components/SettingsHeader.vue";
import { useConfigStore } from "@/stores/config";
import { useUserStore } from "@/stores/user";
import {
  Button,
  createDocumentResource,
  Dialog,
  toast,
  Tooltip,
} from "frappe-ui";
import { computed, h, markRaw, ref } from "vue";
import LucideLock from "~icons/lucide/lock";
import LucideUnlock from "~icons/lucide/unlock";
import AgentCard from "../components/AgentCard.vue";
import Settings from "~icons/lucide/settings-2";
import { router } from "@/router";
import { ConfirmDelete, validateEmail } from "@/utils";
import EmailMultiSelect from "@/components/EmailMultiSelect.vue";
import RenameTeamModal from "./RenameTeamModal.vue";

const routes = computed(() => [
  {
    label: "Teams",
    route: "/settings/teams",
  },
  {
    label: _teamName.value,
    route: `/settings/teams/${team.doc?.name}`,
  },
]);

const { getUser } = useUserStore();
const { teamRestrictionApplied } = useConfigStore();
const invitees = ref<string[]>([]);

const showRename = ref({
  show: false,
  teamName: "",
});

const _teamName = ref(router.currentRoute.value.params.id as string);

const team = createDocumentResource({
  doctype: "HD Team",
  name: router.currentRoute.value.params.id,
  auto: true,
  delete: {
    onSuccess() {
      toast.success("Team deleted");
      router.push({ name: "SettingsTeams" });
    },
  },
  setValue: {
    onSuccess() {
      toast.success("Team updated");
    },
  },
});

const ignoreRestrictions = computed({
  get() {
    return !!team.doc?.ignore_restrictions;
  },
  set(value: boolean) {
    if (!team.doc) return;
    team.setValue.submit({
      ignore_restrictions: value,
    });
  },
});

const teamMembers = computed(() => {
  let users = team.doc?.users || [];
  return users.map((user) => {
    let _user = getUser(user.user);
    return {
      name: user.user,
      user_image: _user.user_image,
      agent_name: _user.full_name,
    };
  });
});

function removeMemberFromTeam(member: string) {
  const users = team.doc?.users?.filter((u) => u.user !== member);
  team.setValue.submit({
    users,
  });
}

function addMember(users: string[]) {
  const _users = team.doc.users.concat(users.map((user) => ({ user })));
  team.setValue.submit({
    users: _users,
  });
  invitees.value = [];
}

const showDelete = ref(false);
const isConfirmingDelete = ref(false);

const memberDropdownOptions = (member) => {
  return ConfirmDelete({
    onConfirmDelete: () => removeMemberFromTeam(member.name),
    isConfirmingDelete,
  });
};

const onRename = async (name) => {
  await router.push({
    name: "EditSettingsTeam",
    params: { id: name },
    replace: true,
    force: true,
  });
  router.go(0);
};

const options = [
  {
    label: "View Assignment rule",
    icon: markRaw(h(Settings, { class: "rotate-90" })),
    onClick: () => {
      router.push({
        name: "EditAssignmentRule",
        params: {
          id: team.doc?.assignment_rule,
        },
        query: {
          previousPage: router.currentRoute.value.fullPath,
        },
      });
    },
  },
  {
    label: "Rename",
    icon: "edit-3",
    onClick: () =>
      (showRename.value = { show: true, teamName: team.doc?.team_name }),
  },
  {
    condition: () => teamRestrictionApplied,
    label: team.doc?.ignore_restrictions
      ? "Disable Bypass Restrictions"
      : "Enable Bypass Restrictions",
    component: () =>
      h(
        Tooltip,
        {
          text: ignoreRestrictions.value
            ? "Members of this team will see the tickets assigned to this team only"
            : "Members of this team will be able to see the tickets assigned to all the teams",
        },
        {
          default: () => [
            //create a div with 2 columns, one for icon and one for label
            h(
              "div",
              {
                class:
                  "flex items-center gap-2 p-2 cursor-pointer hover:bg-gray-100 rounded",
                onClick: () =>
                  (ignoreRestrictions.value = !ignoreRestrictions.value),
              },
              [
                h(team.doc?.ignore_restrictions ? LucideLock : LucideUnlock, {
                  class: "h-4 w-4 text-gray-700",
                  stroke: "currentColor",
                  "aria-hidden": "true",
                }),
                h(
                  "span",
                  {
                    class: "whitespace-nowrap text-ink-gray-7 text-p-base",
                  },
                  [
                    team.doc?.ignore_restrictions
                      ? "Access only this team's tickets"
                      : "Access all team tickets",
                  ]
                ),
              ]
            ),
          ],
        }
      ),
  },
  {
    label: "Delete",
    component: h(Button, {
      label: "Delete",
      variant: "ghost",
      iconLeft: "trash-2",
      theme: "red",
      style: "width: 100%; justify-content: flex-start;",
      onClick: () => {
        showDelete.value = !showDelete.value;
      },
    }),
  },
];
</script>
