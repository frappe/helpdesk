<template>
  <TeamsList v-if="step === 'team-list'" @update:step="updateStep" />
  <NewTeam v-else-if="step === 'new-team'" @update:step="updateStep" />
  <TeamEdit
    v-else-if="step === 'team-edit'"
    @update:step="updateStep"
    :team-name="teamName"
  />
</template>

<script setup lang="ts">
import { onUnmounted, provide, Ref, ref } from "vue";
import TeamEdit from "./TeamEdit.vue";
import TeamsList from "./TeamsList.vue";
import { createListResource } from "frappe-ui";
import NewTeam from "./NewTeam.vue";
import { TeamListResourceSymbol } from "@/types";

type TeamStep = "team-list" | "team-edit" | "new-team";

const step: Ref<TeamStep> = ref("team-list");
const teamName: Ref<string> = ref("");
function updateStep(newStep: TeamStep, team?: string): void {
  step.value = newStep;
  teamName.value = team;
}
const teamsSearchQuery = ref("");

const teams = createListResource({
  doctype: "HD Team",
  cache: ["Teams"],
  fields: ["name"],
  auto: true,
  orderBy: "modified desc",
  start: 0,
  pageLength: 20,
});

provide("teamsSearchQuery", teamsSearchQuery);
provide(TeamListResourceSymbol, teams);

onUnmounted(() => {
  teamsSearchQuery.value = "";
  teams.filters = {};
});
</script>

<style scoped></style>
