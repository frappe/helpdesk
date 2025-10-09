<template>
  <div class="w-full h-full flex flex-col">
    <!-- Header -->
    <div class="px-10 py-8">
      <SettingsLayoutHeader
        title="Teams"
        description="Create and manage teams and assign agents to specific teams."
      >
        <template #actions>
          <Button
            label="New"
            theme="gray"
            variant="solid"
            @click="() => (showForm = !showForm)"
            icon-left="plus"
          />
        </template>
        <template
          v-if="teams.data?.length > 0 || teamsSearchQuery.length"
          #bottom-section
        >
          <div class="relative">
            <Input
              v-model="teamsSearchQuery"
              @input="teamsSearchQuery = $event"
              placeholder="Search"
              type="text"
              class="bg-white hover:bg-white focus:ring-0 border-outline-gray-2"
              icon-left="search"
              debounce="300"
              inputClass="p-4 pr-12"
            />
            <Button
              v-if="teamsSearchQuery"
              icon="x"
              variant="ghost"
              @click="teamsSearchQuery = ''"
              class="absolute right-1 top-1/2 -translate-y-1/2"
            />
          </div>
        </template>
      </SettingsLayoutHeader>
    </div>
    <div class="px-10 pb-8 overflow-y-auto">
      <!-- List -->
      <div
        v-if="!teams.loading && teams.data?.length > 0"
        class="w-full h-full -ml-2"
      >
        <div class="flex text-sm text-gray-600">
          <div class="ml-2">Team name</div>
        </div>
        <hr class="mx-2 mt-2" />
        <div v-for="team in teams.data" :key="team.name">
          <div
            class="flex items-center cursor-pointer hover:bg-gray-50 rounded h-12.5"
          >
            <div
              class="w-full py-3 pl-2"
              @click="() => emit('update:step', 'team-edit', team.name)"
            >
              <div class="text-base text-ink-gray-7 font-medium">
                {{ team.name }}
              </div>
            </div>
            <div class="flex justify-between items-center pr-2">
              <div>
                <Dropdown placement="right" :options="dropdownOptions(team)">
                  <Button
                    icon="more-horizontal"
                    variant="ghost"
                    @click="isConfirmingDelete = false"
                  />
                </Dropdown>
              </div>
            </div>
          </div>
          <hr class="mx-2" />
        </div>
      </div>
      <!-- Loading State -->
      <div
        v-if="teams.loading"
        class="flex mt-28 justify-between w-full h-full"
      >
        <Button
          :loading="teams.loading"
          variant="ghost"
          class="w-full"
          size="2xl"
        />
      </div>
      <!-- Empty State -->
      <div
        v-if="!teams.loading && !teams.data?.length"
        class="flex flex-col items-center justify-center gap-4 p-4 mt-7 h-[500px]"
      >
        <div class="p-4 size-14.5 rounded-full bg-surface-gray-1">
          <AgentIcon class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">No team found</div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{
              teamsSearchQuery.length
                ? "Change your search terms to find teams."
                : "Add your first team to get started."
            }}
          </div>
        </div>
        <Button
          label="Add Team"
          variant="outline"
          icon-left="plus"
          @click="showForm = true"
        />
      </div>
    </div>
  </div>

  <NewTeamModal
    v-model="showForm"
    @create="
      () => {
        teams.reload();
      }
    "
  />
  <RenameTeamModal v-model="showRename" @onRename="() => teams.reload()" />
</template>

<script setup lang="ts">
import { Input, toast } from "frappe-ui";
import { inject, markRaw, Ref, ref, watch } from "vue";
import NewTeamModal from "../NewTeamModal.vue";
import { ConfirmDelete } from "@/utils";
import EditIcon from "@/components/icons/EditIcon.vue";
import RenameTeamModal from "./RenameTeamModal.vue";

interface E {
  (event: "update:step", step: string, team: string): void;
}

const emit = defineEmits<E>();
const teamsSearchQuery = inject<Ref>("teamsSearchQuery");

const teams = inject<any>("teamsData");
const showForm = ref(false);
const showRename = ref({
  show: false,
  teamName: "",
});
const isConfirmingDelete = ref(false);

const dropdownOptions = (team: any) => {
  return [
    {
      label: "Rename",
      icon: markRaw(EditIcon),
      onClick: () => {
        showRename.value = {
          show: true,
          teamName: team.name,
        };
      },
    },
    ...ConfirmDelete({
      onConfirmDelete: () => deleteTeam(team),
      isConfirmingDelete,
    }),
  ];
};

const deleteTeam = (team: any) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }

  teams.delete.submit(team.name, {
    onSuccess: () => {
      toast.success("Team deleted");
    },
  });
};

watch(teamsSearchQuery, (newValue) => {
  teams.filters = {
    name: ["like", `%${newValue}%`],
  };
  if (!newValue) {
    teams.start = 0;
    teams.pageLength = 10;
  }
  teams.reload();
});
</script>
