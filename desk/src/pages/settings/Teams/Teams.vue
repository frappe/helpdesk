<template>
  <SettingsHeader :routes="routes" />
  <div
    class="max-w-3xl xl:max-w-4xl mx-auto w-full px-4 relative flex flex-col-reverse pb-6"
  >
    <div class="w-full h-full flex flex-col gap-6">
      <div class="relative">
        <Input
          v-model="search"
          @input="search = $event"
          placeholder="Search"
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
      <!-- List -->
      <div class="w-full" v-if="!teams.loading && teams.data?.length > 0">
        <div class="grid grid-cols-8 items-center gap-3 text-sm text-gray-600">
          <div class="col-span-6 text-p-sm">Team Name</div>
        </div>
        <hr class="mt-2" />
        <div v-for="team in teams.data" :key="team.name">
          <div
            class="grid grid-cols-8 items-center gap-4 cursor-pointer hover:bg-gray-50 rounded group relative my-1"
          >
            <div
              @click="
                router.push({
                  name: 'EditSettingsTeam',
                  params: { id: team.name },
                })
              "
              class="w-full col-span-7 flex flex-col justify-center h-12.5"
            >
              <div
                class="text-base text-ink-gray-7 font-medium flex items-center gap-2"
              >
                {{ team.name }}
              </div>
            </div>
            <div class="flex justify-end items-center w-full col-span-1 pr-2">
              <div>
                <Dropdown :options="dropdownOptions(team)">
                  <Button
                    icon="more-horizontal"
                    variant="ghost"
                    @click.stop="isConfirmingDelete = false"
                  />
                </Dropdown>
              </div>
            </div>
            <div
              class="absolute -left-2.5 -top-1 w-full h-full group-hover:bg-gray-50 rounded-md z-[-1]"
              :style="{
                width: 'calc(100% + 20px)',
                height: 'calc(100% + 8px)',
              }"
            />
          </div>
          <hr />
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
        <div class="p-4 size-16 rounded-full bg-surface-gray-1">
          <AgentIcon class="size-8 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-lg font-medium text-ink-gray-6">No team found</div>
          <div class="text-base text-ink-gray-5 max-w-60 text-center">
            {{
              search.length
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
    <!-- Header -->
    <div class="bg-white py-4 lg:py-8 lg:pb-6 sticky top-0">
      <SettingsLayoutHeader
        title="Teams"
        description="Create and manage teams and assign agents to specific teams."
      >
        <template #actions>
          <Button
            label="New"
            theme="gray"
            variant="solid"
            @click="() => router.push({ name: 'NewSettingsTeam' })"
            icon-left="plus"
          />
        </template>
        <template #bottom-section v-if="teams.data?.length > 10">
          <FormControl
            v-model="search"
            :placeholder="'Search'"
            type="text"
            :debounce="300"
            class="w-60"
          >
            <template #prefix>
              <LucideSearch class="h-4 w-4 text-gray-500" />
            </template>
          </FormControl>
        </template>
      </SettingsLayoutHeader>
    </div>
    <NewTeamModal
      v-model="showForm"
      @create="
        () => {
          teams.reload();
        }
      "
    />
  </div>
  <RenameTeamModal v-model="showRename" @onRename="() => teams.reload()" />
</template>

<script setup lang="ts">
import { computed, markRaw } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import {
  Button,
  FormControl,
  Input,
  createListResource,
  toast,
} from "frappe-ui";
import { ref, watch } from "vue";
import NewTeamModal from "./NewTeamModal.vue";
import { useRouter } from "vue-router";
import SettingsLayoutHeader from "../components/SettingsLayoutHeader.vue";
import { ConfirmDelete } from "@/utils";
import RenameTeamModal from "./RenameTeamModal.vue";
import { EditIcon } from "@/components/icons";

const router = useRouter();
const routes = computed(() => [
  {
    label: "Teams",
    route: "/settings/teams",
  },
]);
const isConfirmingDelete = ref(false);
const showRename = ref({
  show: false,
  teamName: "",
});

const teams = createListResource({
  doctype: "HD Team",
  cache: ["Teams"],
  fields: ["name"],
  auto: true,
  orderBy: "creation desc",
});

const search = ref("");
const showForm = ref(false);

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

watch(search, (newValue) => {
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
