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
    <!-- List -->
    <div
      v-if="!teams.loading && teams.data?.length > 0"
      class="divide-y w-full"
    >
      <div
        v-for="(team, idx) in teams.data"
        class="flex items-center gap-2 py-2 group justify-between cursor-pointer"
        @click="() => emit('update:step', 'team-edit', team.name)"
      >
        <div class="flex items-center gap-2">
          <Avatar :label="team.name" size="sm" />
          <p :key="team.name" class="text-p-base text-gray-700">
            {{ team.name }}
          </p>
        </div>
        <Button
          icon="trash-2"
          variant="ghost"
          theme="red"
          class="opacity-0"
          @click.stop.self="() => emit('update:step', 'edit', team.name)"
        />
      </div>
    </div>
  </div>
  <NewTeamModal v-model="showForm" @create="() => listViewRef.reload()" />
</template>

<script setup lang="ts">
import { FormControl, createListResource } from "frappe-ui";
import Avatar from "frappe-ui/src/components/Avatar.vue";
import { ref } from "vue";
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
});

const search = ref("");
const showForm = ref(false);
const listViewRef = ref(null);
</script>

<style scoped></style>
