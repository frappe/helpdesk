<template>
  <div v-if="step === 'team-list'" class="h-full">
    <TeamsList @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'team-edit'" class="h-full px-10 py-8">
    <TeamEdit @update:step="updateStep" :team-name="teamName" />
  </div>
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
