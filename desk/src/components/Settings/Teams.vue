<template>
  <div class="w-full h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between mb-7">
      <h1 class="text-lg font-semibold">Teams</h1>
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
        <Button
          @click="() => (showForm = !showForm)"
          label="New"
          variant="solid"
        >
          <template #prefix>
            <LucidePlus class="h-4 w-4 stroke-1.5" />
          </template>
        </Button>
      </div>
    </div>

    <div class="overflow-y-auto w-full hide-scrollbar h-full">
      <div v-for="(team, idx) in filteredTeams" :key="team.name">
        <div
          class="flex flex-col gap-2 mb-2"
          :class="idx !== filteredTeams.length - 1 && 'border-b '"
        >
          <div class="flex items-center justify-between">
            <p class="text-base font-semibold text-ink-gray-8">
              {{ team?.name }}
            </p>
            <Dropdown
              placement="right"
              :options="getDropdownOptions(team.name)"
            >
              <Button icon="more-horizontal" variant="ghost" />
            </Dropdown>
          </div>
          <div class="flex flex-col divide-y" v-if="team.members.length">
            <!-- Pill team member -->
            <div
              v-for="member in team.members"
              class="flex items-center gap-1 py-3 pl-1 justify-between group"
            >
              <div class="flex items-center gap-2">
                <Avatar
                  :label="member.user"
                  size="sm"
                  :image="getUser(member.user)?.user_image"
                />
                <p class="text-p-base text-gray-700">{{ member.user }}</p>
              </div>
              <Button
                icon-left="x"
                label="Remove"
                variant="ghost"
                class="opacity-0 group-hover:opacity-100"
                @click.stop="() => removeMemberFromTeam(team.name, member.user)"
              />
            </div>
          </div>
          <!-- Emtyp state -->
          <div v-if="team.members.length === 0" class="flex py-2">
            <p class="text-sm text-gray-500">No members found</p>
          </div>
        </div>
      </div>
    </div>
  </div>
  <NewTeamModal v-model="showForm" @create="() => teams.reload()" />
  <AddMemberModal
    v-model="addMemberModal"
    :team="teamDocuments[selectedTeam]"
  />
</template>

<script setup lang="ts">
import { globalStore } from "@/stores/globalStore";
import { useUserStore } from "@/stores/user";
import { createToast } from "@/utils";
import {
  Avatar,
  Button,
  createDocumentResource,
  createResource,
  Dropdown,
  FormControl,
} from "frappe-ui";
import { computed, ref } from "vue";
import AddMemberModal from "./AddMemberModal.vue";
import NewTeamModal from "./NewTeamModal.vue";
import { teamDocuments } from "./teams";
const { $dialog } = globalStore();
const { getUser } = useUserStore();

const showForm = ref(false);
const addMemberModal = ref(false);
const search = ref("");

const teams = createResource({
  url: "helpdesk.helpdesk.doctype.hd_team.hd_team.get_teams",
  cache: ["Teams"],
  auto: true,
  onSuccess: (data) => {
    data.forEach((team) => {
      if (teamDocuments.value[team.name]) return;
      teamDocuments.value[team.name] = createDocumentResource({
        doctype: "HD Team",
        name: team.name,
        cache: ["HD Team", team.name],
      });
    });
  },
});

const selectedTeam = ref(null);

function getDropdownOptions(teamName: string) {
  return [
    {
      label: "Add Member",
      icon: "plus",
      onClick: () => {
        showForm.value = true;
        selectedTeam.value = teamName;
        addMemberModal.value = true;
      },
    },
    {
      label: "Rename",
      icon: "edit-2",
      onClick: () => {
        console.log("Rename", teamName);
      },
    },
    {
      label: "Delete",
      icon: "trash-2",
      onClick: () => deleteTeam(teamName),
    },
  ];
}

const filteredTeams = computed(() => {
  if (!teams.data) return [];

  if (!search.value) return teams.data;

  const searchTerm = search.value.toLowerCase();
  return teams.data.filter((team) => {
    // Search by team name
    if (team.name.toLowerCase().includes(searchTerm)) return true;

    // Search by member name/email
    return team.members.some((member) =>
      member.user.toLowerCase().includes(searchTerm)
    );
  });
});

async function removeMemberFromTeam(teamName: string, member: string) {
  const team = teamDocuments.value[teamName];
  if (!team) return;
  const users = team.doc?.users?.filter((u) => u.user !== member);
  await team.setValue.submit({
    users,
  });
  teams.reload();
}

async function deleteTeam(teamName: string) {
  const team = teamDocuments.value[teamName];
  if (!team) return;
  $dialog({
    title: "Delete",
    message: `Are you sure you want to delete the team ${teamName}?`,
    actions: [
      {
        label: "Confirm",
        variant: "solid",
        onClick: async (close) => {
          close();
          createToast({
            title: "Team deleted successfully",
            icon: "check",
            iconClasses: "text-green-600",
          });
          await team.delete.submit();
          teams.reload();
        },
      },
    ],
  });
}
</script>

<style scoped></style>
