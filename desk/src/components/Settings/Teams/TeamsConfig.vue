<template>
  <TeamsList v-if="step === 'team-list'" @update:step="updateStep" />
  <TeamEdit
    v-else-if="step === 'team-edit'"
    @update:step="updateStep"
    :team-name="teamName"
  />
</template>

<script setup lang="ts">
import { onMounted, provide, Ref, ref } from "vue";
import TeamEdit from "./TeamEdit.vue";
import TeamsList from "./TeamsList.vue";
import { createListResource } from "frappe-ui";

type TeamStep = "team-list" | "team-edit";

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
  orderBy: "creation desc",
  start: 0,
  pageLength: 20,
});

provide("teamsSearchQuery", teamsSearchQuery);
provide("teamsData", teams);

onMounted(() => {
  teamsSearchQuery.value = "";
  teams.filters = {};
  teams.reload();
});
</script>

<style scoped></style>
