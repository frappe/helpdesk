<template>
  <div v-if="step === 'team-list'" class="h-full">
    <TeamsList @update:step="updateStep" />
  </div>
  <div v-else-if="step === 'team-edit'" class="h-full">
    <TeamEdit @update:step="updateStep" :team-name="teamName" />
  </div>
</template>

<script setup lang="ts">
import { Ref, ref } from "vue";
import TeamEdit from "./TeamEdit.vue";
import TeamsList from "./TeamsList.vue";

type TeamStep = "team-list" | "team-edit";

const step: Ref<TeamStep> = ref("team-list");
const teamName: Ref<string> = ref("");
function updateStep(newStep: TeamStep, team?: string): void {
  step.value = newStep;
  teamName.value = team;
}
</script>

<style scoped></style>
