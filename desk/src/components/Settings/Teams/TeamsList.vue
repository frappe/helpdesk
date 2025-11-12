<template>
  <SettingsLayoutBase
    :title="__('Teams')"
    :description="
      __('Create and manage teams and assign agents to specific teams.')
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        @click="emit('update:step', 'new-team', '')"
        icon-left="plus"
      />
    </template>
    <template
      v-if="teams.data?.length > 9 || teamsSearchQuery.length"
      #header-bottom
    >
      <div class="relative">
        <Input
          :model-value="teamsSearchQuery"
          @input="teamsSearchQuery = $event"
          :placeholder="__('Search')"
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
    <template #content>
      <!-- List -->
      <div
        v-if="!teams.loading && teams.data?.length > 0"
        class="w-full h-full -ml-2"
      >
        <div class="flex text-sm text-gray-600">
          <div class="ml-2">{{ __("Team name") }}</div>
        </div>
        <hr class="mx-2 mt-2" />
        <div v-for="(team, index) in teams.data" :key="team.name">
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
          <hr v-if="index !== teams.data.length - 1" class="mx-2" />
        </div>
        <!-- Load More Button -->
        <div class="flex justify-center">
          <Button
            v-if="!teams.loading && teams.hasNextPage"
            class="mt-3.5 p-2"
            @click="() => teams.next()"
            :loading="teams.loading"
            :label="__('Load More')"
            icon-left="refresh-cw"
          />
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
        class="flex flex-col items-center justify-center gap-4 h-full"
      >
        <div
          class="p-4 size-14.5 rounded-full bg-surface-gray-1 flex justify-center items-center"
        >
          <AgentIcon class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No team found") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 max-w-60 text-center">
            {{
              teamsSearchQuery.length
                ? __("Change your search terms to find teams.")
                : __("Add one to get started.")
            }}
          </div>
        </div>
        <Button
          :label="__('New')"
          variant="outline"
          icon-left="plus"
          @click="showForm = true"
        />
      </div>
    </template>
  </SettingsLayoutBase>
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
import { Dropdown, Input, toast } from "frappe-ui";
import { inject, markRaw, Ref, ref, watch } from "vue";
import NewTeamModal from "../NewTeamModal.vue";
import { ConfirmDelete } from "@/utils";
import EditIcon from "@/components/icons/EditIcon.vue";
import RenameTeamModal from "./RenameTeamModal.vue";
import { __ } from "@/translation";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { TeamListResourceSymbol } from "@/types";

interface E {
  (event: "update:step", step: string, team: string): void;
}

const emit = defineEmits<E>();
const teamsSearchQuery = inject<Ref>("teamsSearchQuery");

const teams = inject(TeamListResourceSymbol);
const showForm = ref(false);
const showRename = ref({
  show: false,
  teamName: "",
});
const isConfirmingDelete = ref(false);

const dropdownOptions = (team: any) => {
  return [
    {
      label: __("Rename"),
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
      toast.success(__("Team deleted"));
    },
  });
};

watch(teamsSearchQuery, (newValue) => {
  teams.filters = {
    ...teams.filters,
    name: ["like", `%${newValue}%`],
  };
  teams.reload();
});
</script>
