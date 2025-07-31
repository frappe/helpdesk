<template>
  <div class="w-full h-full flex flex-col">
    <!-- Header -->
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
      <template #bottom-section>
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
    <!-- List -->
    <div
      v-if="!teams.loading && teams.data?.length > 0"
      class="divide-y w-full h-full hide-scrollbar overflow-y-scroll mt-4"
    >
      <div
        v-for="team in teams.data"
        :key="team.name"
        class="flex items-center gap-2 py-2 group justify-between cursor-pointer"
        @click="() => emit('update:step', 'team-edit', team.name)"
      >
        <div class="flex items-center gap-2">
          <Avatar :label="team.name" size="sm" />
          <p :key="team.name" class="text-p-base text-gray-700">
            {{ team.name }}
          </p>
        </div>
      </div>
    </div>
    <!-- Loading State -->
    <div v-if="teams.loading" class="flex mt-28 justify-between w-full h-full">
      <Button
        :loading="teams.loading"
        variant="ghost"
        class="w-full"
        size="2xl"
      />
    </div>
    <!-- Empty State -->
    <div
      v-if="!teams.data?.length"
      class="flex mt-28 justify-between w-full h-full"
    >
      <p class="text-sm text-gray-500 w-full flex justify-center">
        No teams found
      </p>
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
</template>

<script setup lang="ts">
import { Avatar, FormControl, createListResource } from "frappe-ui";
import { ref, watch } from "vue";
import NewTeamModal from "../NewTeamModal.vue";

interface E {
  (event: "update:step", step: string, team: string): void;
}

const emit = defineEmits<E>();

const teams = createListResource({
  doctype: "HD Team",
  cache: ["Teams"],
  fields: ["name"],
  auto: true,
  orderBy: "creation desc",
});

const search = ref("");
const showForm = ref(false);

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

<style scoped></style>
