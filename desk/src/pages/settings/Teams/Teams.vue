<template>
  <SettingsHeader :routes="routes" />
  <div class="w-full max-w-3xl xl:max-w-4xl mx-auto p-4 lg:py-8">
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
      <!-- List -->
      <div
        v-if="!teams.loading && teams.data?.length > 0"
        class="divide-y w-full h-full hide-scrollbar overflow-y-scroll mt-4"
      >
        <div
          v-for="team in teams.data"
          :key="team.name"
          class="flex items-center gap-2 py-3 group justify-between cursor-pointer"
          @click="
            () =>
              router.push({
                name: 'EditSettingsTeam',
                params: { id: team.name },
              })
          "
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
        v-if="!teams.data?.length"
        class="flex flex-col items-center justify-center gap-3 rounded-md border border-gray-200 p-4 mt-7 h-[500px]"
      >
        <div class="text-lg font-medium text-ink-gray-4">No Teams found</div>
        <Button
          label="Add Team"
          variant="subtle"
          icon-left="plus"
          @click="showForm = true"
        />
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
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SettingsHeader from "../components/SettingsHeader.vue";
import { Avatar, FormControl, createListResource } from "frappe-ui";
import { ref, watch } from "vue";
import NewTeamModal from "./NewTeamModal.vue";
import { useRouter } from "vue-router";
import SettingsLayoutHeader from "../components/SettingsLayoutHeader.vue";

const router = useRouter();
const routes = computed(() => [
  {
    label: "Teams",
    route: "/settings/teams",
  },
]);

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
